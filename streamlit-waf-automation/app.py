import os
import json as _json
import time as _time
import requests
import streamlit as st

# Set page config
st.set_page_config(
    page_title="WAF Assessment Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "waf_page" not in st.session_state:
    st.session_state.waf_page = "dashboard"
# Only read query params on first load, not after user-driven navigation
if not st.session_state.get("_nav_by_user"):
    try:
        _qp = st.query_params.get("page")
        if _qp == "recommendations":
            st.session_state.waf_page = "recommendations"
        elif _qp == "progress":
            st.session_state.waf_page = "progress"
        elif _qp == "genie_readiness":
            st.session_state.waf_page = "genie_readiness"
    except Exception:
        pass

# Dashboard configuration — injected via app.yaml env vars at deploy time
INSTANCE_URL = os.environ.get("WAF_INSTANCE_URL", "")
DASHBOARD_ID = os.environ.get("WAF_DASHBOARD_ID", "")
WORKSPACE_ID = os.environ.get("WAF_WORKSPACE_ID", "")
EMBED_URL = f"{INSTANCE_URL}/embed/dashboardsv3/{DASHBOARD_ID}?o={WORKSPACE_ID}" if DASHBOARD_ID else ""

# Reload job config — injected via app.yaml env vars at deploy time
JOB_ID       = os.environ.get("WAF_JOB_ID", "")
WAREHOUSE_ID = os.environ.get("WAF_WAREHOUSE_ID", "")
GENIE_URL    = os.environ.get("WAF_GENIE_URL", "")


def _get_ws_client():
    """Return a WorkspaceClient auto-configured from the runtime environment."""
    try:
        from databricks.sdk import WorkspaceClient
        return WorkspaceClient()
    except Exception:
        return None


def _load_run_info():
    """Return latest successful run info from _run_log, or {} if unavailable."""
    _cat = os.environ.get("WAF_CATALOG", "useast1")
    if not WAREHOUSE_ID:
        return {}
    _wc = _get_ws_client()
    if _wc:
        try:
            from databricks.sdk.service.sql import StatementState
            _stmt = (
                f"SELECT run_id, triggered_at, finished_at, status, "
                f"tables_succeeded, tables_failed "
                f"FROM `{_cat}`.`waf_cache`.`_run_log` "
                f"WHERE status IN ('success','partial') "
                f"ORDER BY run_id DESC LIMIT 1"
            )
            _r = _wc.statement_execution.execute_statement(
                statement=_stmt,
                warehouse_id=WAREHOUSE_ID,
                wait_timeout="50s",
            )
            if (_r.status and _r.status.state == StatementState.SUCCEEDED
                    and _r.result and _r.result.data_array):
                row = _r.result.data_array[0]
                return {
                    "run_id": row[0], "triggered_at": row[1], "finished_at": row[2],
                    "status": row[3], "tables_succeeded": int(row[4] or 0),
                    "tables_failed": int(row[5] or 0), "catalog": _cat,
                }
        except Exception:
            pass
    return {}


# Sidebar with explanations
import csv as _csv

def _load_waf_controls():
    """Load WAF controls from CSV file next to app.py."""
    _csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "waf_controls_with_recommendations.csv")
    try:
        with open(_csv_path, encoding="utf-8") as _f:
            return list(_csv.DictReader(_f))
    except Exception as _e:
        return []

_ALL_CONTROLS = _load_waf_controls()


# ── Genie Readiness helpers ───────────────────────────────────────────────────

def _to_bool(v):
    """Normalize boolean values that may arrive as Python bool or 'true'/'false' string."""
    if isinstance(v, bool):
        return v
    return str(v).lower() == "true"


def _run_genie_readiness_checks(wc, warehouse_id):
    """
    Run all Genie Readiness SQL checks live against system tables.
    Returns a dict of results; any key may be missing/None if the query failed.
    Requires: SELECT on system.access, system.billing, system.information_schema, system.query.
    """
    from databricks.sdk.service.sql import StatementState

    results = {}

    def _exec(sql, tag):
        """
        Execute a SQL statement and return the first row as a dict.
        wait_timeout="50s" gives cold warehouses (30-60s start) time to respond.
        All Genie Readiness queries are designed to finish in < 30s on a warm warehouse.
        """
        try:
            r = wc.statement_execution.execute_statement(
                statement=sql, warehouse_id=warehouse_id, wait_timeout="50s"
            )
            if (r.status and r.status.state == StatementState.SUCCEEDED
                    and r.result and r.result.data_array):
                cols = [c.name for c in r.manifest.schema.columns]
                return dict(zip(cols, r.result.data_array[0]))
            # Surface query failures for the error expander
            if r.status and r.status.state not in (
                    StatementState.RUNNING, StatementState.PENDING):
                _err_detail = ""
                if r.status.error:
                    _err_detail = (r.status.error.message or "")[:150]
                _state_name = getattr(r.status.state, "value", str(r.status.state))
                results[f"_err_{tag}"] = f"[{_state_name}] {_err_detail}".strip()
        except Exception as e:
            results[f"_err_{tag}"] = str(e)[:200]
        return None

    # ── 1. Unity Catalog ─────────────────────────────────
    row = _exec(
        "SELECT COUNT(*) AS uc_count "
        "FROM system.information_schema.catalogs "
        "WHERE catalog_name != 'hive_metastore'",
        "uc",
    )
    if row:
        results["uc_count"] = int(row.get("uc_count") or 0)

    # ── 2. Premium / Enterprise plan (SKU prefix) ────────
    row = _exec(
        """SELECT CASE
             WHEN COUNT(CASE WHEN sku_name LIKE 'ENTERPRISE%' THEN 1 END) > 0 THEN 'Enterprise'
             WHEN COUNT(CASE WHEN sku_name LIKE 'PREMIUM%'    THEN 1 END) > 0 THEN 'Premium'
             WHEN COUNT(CASE WHEN sku_name LIKE 'STANDARD%'   THEN 1 END) > 0 THEN 'Standard'
             ELSE 'Unknown'
           END AS plan_tier
           FROM system.billing.usage
           WHERE usage_date >= current_date() - 30""",
        "plan",
    )
    if row:
        results["plan_tier"] = row.get("plan_tier", "Unknown")

    # ── 3. Audit log: AIM, SCIM, login type, group cloning, Genie MAU ──────
    # Single-scan approach: one pass over system.access.audit filtered to only
    # the services and action_names we actually need.  Five separate CTEs each
    # trigger a full table scan; the conditional-aggregation pattern below does
    # it in one — dramatically faster on large audit tables (1B+ rows).
    audit_sql = """
    SELECT
      -- AIM (30-day window; externalId user check covers "configured but not recently run")
      COUNT(CASE WHEN service_name = 'aimControlPolicy'
                 THEN 1 END) > 0                                            AS aim_configured,
      MAX(CASE WHEN service_name = 'aimControlPolicy'
               THEN event_time END)                                         AS last_aim_event,

      -- SCIM provisioning (30-day window, Okta/SCIM/Azure user-agents)
      COUNT(CASE WHEN service_name = 'accounts'
                  AND action_name IN ('createUser','updateUser','addPrincipalToGroup')
                  AND (user_agent LIKE '%SCIM%'
                       OR user_agent LIKE '%Okta%'
                       OR user_agent LIKE '%Azure%')
                 THEN 1 END) > 0                                            AS scim_active,
      MAX(CASE WHEN service_name = 'accounts'
                AND action_name IN ('createUser','updateUser','addPrincipalToGroup')
                AND (user_agent LIKE '%SCIM%'
                     OR user_agent LIKE '%Okta%'
                     OR user_agent LIKE '%Azure%')
               THEN event_time END)                                         AS last_scim_event,

      -- Federated / browser SSO login (30-day window)
      COUNT(CASE WHEN service_name = 'accounts'
                  AND event_date >= current_date() - 30
                  AND action_name IN ('aadBrowserLogin','samlLogin','oidcBrowserLogin')
                 THEN 1 END) > 0                                            AS federated_login,
      CASE
        WHEN COUNT(CASE WHEN service_name = 'accounts'
                         AND event_date >= current_date() - 30
                         AND action_name = 'aadBrowserLogin' THEN 1 END) > 0
             THEN 'Microsoft Entra ID'
        WHEN COUNT(CASE WHEN service_name = 'accounts'
                         AND event_date >= current_date() - 30
                         AND action_name = 'samlLogin' THEN 1 END) > 0
             THEN 'SAML'
        WHEN COUNT(CASE WHEN service_name = 'accounts'
                         AND event_date >= current_date() - 30
                         AND action_name = 'oidcBrowserLogin' THEN 1 END) > 0
             THEN 'OIDC'
        ELSE 'Not detected'
      END                                                                   AS idp_type,

      -- Group cloning / IdP group sync (30-day window)
      COUNT(CASE WHEN service_name = 'accounts'
                  AND event_date >= current_date() - 30
                  AND action_name IN ('createGroup','addPrincipalToGroup',
                                      'removePrincipalFromGroup')
                  AND (request_params['endpoint'] = 'autoUserCreation'
                       OR user_agent LIKE '%SCIM%'
                       OR user_agent LIKE '%Okta%')
                 THEN 1 END) > 0                                            AS group_cloning_active,
      COUNT(DISTINCT CASE WHEN service_name = 'accounts'
                           AND event_date >= current_date() - 30
                           AND action_name IN ('createGroup','addPrincipalToGroup',
                                               'removePrincipalFromGroup')
                           AND (request_params['endpoint'] = 'autoUserCreation'
                                OR user_agent LIKE '%SCIM%'
                                OR user_agent LIKE '%Okta%')
                          THEN request_params['targetGroupName'] END)       AS synced_group_count,

      -- Genie MAU (30-day window)
      COUNT(DISTINCT CASE WHEN service_name = 'aibiGenie'
                           AND event_date >= current_date() - 30
                           AND action_name IN ('genieStartConversationMessage',
                                               'genieCreateConversationMessage')
                          THEN user_identity.email END)                     AS genie_mau,
      COUNT(CASE WHEN service_name = 'aibiGenie'
                  AND event_date >= current_date() - 30
                  AND action_name IN ('genieStartConversationMessage',
                                      'genieCreateConversationMessage')
                 THEN 1 END)                                                AS genie_messages,
      COUNT(CASE WHEN service_name = 'aibiGenie'
                  AND event_date >= current_date() - 7
                  AND action_name IN ('genieStartConversationMessage',
                                      'genieCreateConversationMessage')
                 THEN 1 END)                                                AS msgs_last_7d,
      COUNT(CASE WHEN service_name = 'aibiGenie'
                  AND event_date BETWEEN current_date() - 14 AND current_date() - 8
                  AND action_name IN ('genieStartConversationMessage',
                                      'genieCreateConversationMessage')
                 THEN 1 END)                                                AS msgs_prev_7d

    FROM system.access.audit
    WHERE event_date >= current_date() - 30
      AND (
        service_name = 'aimControlPolicy'
        OR (service_name = 'aibiGenie'
            AND action_name IN ('genieStartConversationMessage',
                                'genieCreateConversationMessage'))
        OR (service_name = 'accounts'
            AND action_name IN (
              'createUser','updateUser','addPrincipalToGroup','removePrincipalFromGroup',
              'aadBrowserLogin','samlLogin','oidcBrowserLogin',
              'createGroup'
            ))
      )
    """
    row = _exec(audit_sql, "audit")
    if row:
        results.update({
            "aim_configured":      _to_bool(row.get("aim_configured")),
            "last_aim_event":      row.get("last_aim_event"),
            "scim_active":         _to_bool(row.get("scim_active")),
            "last_scim_event":     row.get("last_scim_event"),
            "federated_login":     _to_bool(row.get("federated_login")),
            "idp_type":            row.get("idp_type", "Not detected"),
            "group_cloning_active": _to_bool(row.get("group_cloning_active")),
            "synced_group_count":  int(row.get("synced_group_count") or 0),
            "genie_mau":           int(row.get("genie_mau") or 0),
            "genie_messages":      int(row.get("genie_messages") or 0),
            "msgs_last_7d":        int(row.get("msgs_last_7d") or 0),
            "msgs_prev_7d":        int(row.get("msgs_prev_7d") or 0),
        })

    # ── 4. Consumer / SQL-only users (behavioral proxy) ──
    # system.query.history uses `executed_by` (not `user_name`) for the running user.
    row = _exec(
        """SELECT COUNT(DISTINCT executed_by) AS sql_only_users
           FROM system.query.history
           WHERE start_time >= current_timestamp() - INTERVAL 30 DAYS
             AND compute.type = 'WAREHOUSE'
             AND executed_by NOT IN (
               SELECT DISTINCT user_identity.email
               FROM system.access.audit
               WHERE service_name = 'clusters'
                 AND action_name IN ('create','start')
                 AND event_date >= current_date() - 30
             )""",
        "sql_only",
    )
    if row:
        results["sql_only_users"] = int(row.get("sql_only_users") or 0)

    # ── 5. SCIM detection via users/groups externalId ────
    # Audit-log SCIM check can miss account-level SCIM provisioning which runs
    # at the account tier and may not surface as workspace-scoped audit events.
    # Checking for externalId on users/groups is the canonical, reliable signal.
    _scim_detected, _scim_detail, _scim_err = _check_scim_via_users_api(wc)
    # Store as-is (True | None) — do NOT wrap in bool() or None becomes False
    results["scim_users_detected"] = _scim_detected
    results["scim_users_detail"]   = _scim_detail
    if _scim_err:
        results["_err_scim_users"] = _scim_err

    return results


def _check_scim_via_users_api(wc):
    """
    Attempt to detect SCIM provisioning via workspace users/groups API.

    IMPORTANT LIMITATION: Databricks stores externalId at the ACCOUNT level.
    The workspace SCIM API (/api/2.0/preview/scim/v2/Users) does NOT expose
    externalId even when account-level SCIM (Okta/Entra) is fully configured.
    This function can only confirm workspace-level SCIM; for account-level SCIM
    it returns None (indeterminate) — never a false ❌.

    Returns:
      (True,  detail, None)  — externalId found → workspace SCIM confirmed
      (None,  detail, None)  — no externalId but users/groups exist → indeterminate
                               (account-level SCIM cannot be detected via workspace API)
      (None,  "",     err)   — API call failed
    """
    user_count = 0
    scim_user_count = 0
    try:
        for u in wc.users.list(attributes="id,externalId"):
            user_count += 1
            if getattr(u, "external_id", None):
                scim_user_count += 1
            if user_count >= 200:
                break
        if scim_user_count > 0:
            return True, f"{scim_user_count}/{user_count} user(s) with externalId (workspace SCIM-managed)", None
    except Exception as e:
        return None, "", str(e)[:120]

    grp_count = 0
    scim_grp_count = 0
    try:
        for g in wc.groups.list(attributes="id,externalId"):
            grp_count += 1
            if getattr(g, "external_id", None):
                scim_grp_count += 1
            if grp_count >= 200:
                break
        if scim_grp_count > 0:
            return True, f"{scim_grp_count}/{grp_count} group(s) with externalId (workspace SCIM-managed)", None
    except Exception as e:
        return None, "", str(e)[:120]

    # No externalId found.  If there are users/groups, account-level SCIM is plausible
    # but undetectable from the workspace API — return None (indeterminate), never False.
    total = user_count + grp_count
    if total > 0:
        return None, (
            f"{user_count} user(s) · {grp_count} group(s) in workspace. "
            "Account-level SCIM cannot be detected via workspace API — "
            "verify in Admin Console → Identity & Access"
        ), None

    # Truly empty workspace (very unusual)
    return None, "No users or groups found in workspace", None


def _check_unified_login(wc):
    """
    Try the workspace Settings API for Unified Login status.
    Returns True (enabled), False (disabled), or None (403 / not determinable).
    """
    try:
        data = wc.api_client.do(
            "GET", "/api/2.0/settings/types/unified_login/names/default"
        )
        return bool(data.get("unified_login_config", {}).get("enabled", False))
    except Exception as e:
        # 403 = needs workspace admin — expected, not an error
        return None


def _compute_readiness_tier(r):
    """
    Compute 3-tier Genie Readiness from the results dict.
    Returns (tier, core_flags, genie_flags) where each flags list is list[bool].
      tier: 'green' | 'yellow' | 'red'
    """
    has_uc      = (r.get("uc_count") or 0) > 0
    has_premium = r.get("plan_tier", "Unknown") in ("Premium", "Enterprise")

    # ── Audit-based checks: False could mean RLS (SP sees only own events) ──────
    # We can't distinguish "not configured" from "SP lacks audit GRANT" from within
    # the app. Treat False as indeterminate (is not False = pass in tier logic) so
    # the workspace isn't stuck at 🔴 solely because of missing SP grants.
    # Once grants are applied and Re-check is clicked, True/False will be accurate.

    _scim_det = r.get("scim_users_detected")   # True | None (never False after fix)
    has_provisioning = (
        r.get("aim_configured", False)
        or r.get("scim_active", False)
        or _scim_det is not False   # True or None → don't block tier
    )

    # federated_login is a plain bool from the audit SQL
    has_federation = r.get("federated_login", False) or None  # False→None (indeterminate)

    # For tier: treat None (indeterminate) as passing; only confirmed False blocks
    core = [
        has_uc,
        has_premium,
        has_provisioning is not False,
        has_federation is not False,   # None is not False → True
    ]

    has_sql_users     = (r.get("sql_only_users") or 0) > 0
    has_group_cloning = r.get("group_cloning_active", False)
    genie_criteria    = [has_sql_users, has_group_cloning]

    if all(core) and all(genie_criteria):
        return "green", core, genie_criteria
    elif all(core):
        return "yellow", core, genie_criteria
    else:
        return "red", core, genie_criteria


# ── End Genie Readiness helpers ───────────────────────────────────────────────


_PILLAR_PREFIXES = {
    "📊 Summary": None,
    "🔐 Data & AI Governance": "DG",
    "💰 Cost Optimization": "CO",
    "⚡ Performance Efficiency": "PE",
    "🛡️ Reliability": "R",
}

with st.sidebar:
    st.title("📖 WAF Guide")

    category = st.selectbox(
        "Select category:",
        list(_PILLAR_PREFIXES.keys())
    )

    st.markdown("---")

    if category == "📊 Summary":
        st.markdown("""
        ### WAF Assessment Overview

        The dashboard measures your environment across 4 pillars:

        **🔐 Data & AI Governance** (25%)
        - Table security & access control
        - Data quality & lineage
        - PII protection

        **💰 Cost Optimization** (25%)
        - Compute efficiency
        - Storage optimization
        - Resource utilization

        **⚡ Performance Efficiency** (25%)
        - Query optimization
        - Cluster performance
        - Photon adoption

        **🛡️ Reliability** (25%)
        - System availability
        - Auto-recovery
        - Production readiness

        ### How Overall Score is Calculated

        The **Overall WAF Score** is calculated by:

        1. **Individual Pillar Scores**: Each pillar calculates its completion percentage
           - Counts how many WAF controls are "Pass" (meet threshold)
           - Formula: `(Passed Controls / Total Controls) × 100`

        2. **Summary Aggregation**: Combines all 4 pillar scores
           - Each pillar contributes equally (25% weight)
           - Shows individual pillar scores for comparison

        3. **Score Interpretation**:
           - 🎯 **80%+**: Excellent - Production-ready
           - 🟨 **60-80%**: Good - Minor improvements needed
           - 🟧 **40-60%**: Needs improvement - Address gaps
           - 🔴 **<40%**: Critical gaps - Immediate action required

        ### Target Scores
        - 🎯 **80%+**: Excellent
        - 🟨 **60-80%**: Good
        - 🟧 **40-60%**: Needs improvement
        - 🔴 **<40%**: Critical gaps

        ### Actions
        Select a pillar above to see:
        - How each metric is calculated
        - Thresholds for each control
        - Specific actions if your score is low
        """)
    
    else:
        _prefix = _PILLAR_PREFIXES[category]
        _pillar_controls = [r for r in _ALL_CONTROLS if r.get("waf_id", "").startswith(_prefix)]

        def _short_label(row):
            """Return the best short label for a control row.
            DG/CO/PE store the short phrase in 'best_practice';
            R controls store it in 'pillar_name' (best_practice is a long paragraph).
            We pick the shorter, non-empty field."""
            bp = (row.get("best_practice") or "").strip()
            pn = (row.get("pillar_name") or "").strip()
            # If best_practice is a short phrase (≤120 chars) prefer it, else use pillar_name
            if bp and len(bp) <= 120:
                return bp
            if pn and len(pn) <= 120:
                return pn
            return bp[:120] if bp else pn[:120]

        if not _pillar_controls:
            st.warning(f"No controls found for pillar **{category}**. Check that `waf_controls_with_recommendations.csv` is present next to `app.py`.")
        else:
            _options = [f"{r['waf_id']} — {_short_label(r)}" for r in _pillar_controls]
            _selected_label = st.selectbox("Select control:", _options)
            _waf_id = _selected_label.split(" — ")[0].strip()
            _ctrl = next((r for r in _pillar_controls if r.get("waf_id") == _waf_id), None)

            if _ctrl:
                _label = _short_label(_ctrl)
                st.markdown(f"### {_ctrl['waf_id']} — {_label}")

                _principle = _ctrl.get("principle", "").strip()
                if _principle:
                    st.markdown(f"**Capability**: {_principle}")

                _threshold = _ctrl.get("threshold_percentage", "").strip()
                if _threshold:
                    st.markdown(f"**Threshold**: ≥{_threshold}% to pass")

                _metric_def = _ctrl.get("metric_definition", "").strip()
                if _metric_def:
                    st.markdown("**What it measures**")
                    st.markdown(_metric_def)

                _rec = _ctrl.get("recommendation_if_not_met", "").strip()
                if _rec:
                    with st.expander("Recommendation if Not Met"):
                        st.markdown(_rec)
            else:
                st.info("Select a control above to see details.")


# --- Run info (needed for catalog/warehouse on both pages) ---
_run_info = _load_run_info()
_catalog = _run_info.get("catalog") or os.environ.get("WAF_CATALOG", "useast1")
_schema = "waf_cache"

# Main content: Dashboard vs Recommendations vs Progress page
if st.session_state.waf_page == "progress":
    st.title("WAF Assessment Progress")
    st.markdown("Total score over time (average across pillars per run).")
    st.markdown("---")
    if st.button("← Back to Dashboard", type="secondary", key="back_progress"):
        st.session_state.waf_page = "dashboard"
        st.session_state._nav_by_user = True
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()
    if not WAREHOUSE_ID:
        st.warning("No warehouse configured (WAF_WAREHOUSE_ID). Run install and set app env vars.")
    else:
        _wc = _get_ws_client()
        if not _wc:
            st.error("Databricks SDK could not initialise.")
        else:
            try:
                from databricks.sdk.service.sql import StatementState
                _stmt = (
                    f"SELECT r.run_id, r.triggered_at, ROUND(avg_score.overall_score, 2) AS overall_score "
                    f"FROM `{_catalog}`.`{_schema}`.`_run_log` r "
                    f"INNER JOIN ("
                    f"  SELECT _run_id, AVG(completion_percent) AS overall_score "
                    f"  FROM `{_catalog}`.`{_schema}`.waf_total_percentage_across_pillars_hist "
                    f"  GROUP BY _run_id"
                    f") avg_score ON avg_score._run_id = r.run_id "
                    f"WHERE r.status IN ('success', 'partial') "
                    f"ORDER BY r.run_id"
                )
                _r = _wc.statement_execution.execute_statement(
                    statement=_stmt,
                    warehouse_id=WAREHOUSE_ID,
                    wait_timeout="20s",
                )
                if _r.status and _r.status.state == StatementState.SUCCEEDED and _r.result and _r.result.data_array:
                    rows = _r.result.data_array
                    cols = None
                    for _src in (_r.result, _r):
                        if getattr(_src, "manifest", None) and getattr(_src.manifest, "schema", None) and getattr(_src.manifest.schema, "columns", None):
                            cols = [c.name for c in (_src.manifest.schema.columns or [])]
                            break
                    if not cols and rows:
                        cols = ["run_id", "triggered_at", "overall_score"] if len(rows[0]) == 3 else [f"col{i}" for i in range(len(rows[0]))]
                    import pandas as pd
                    labels = []
                    scores = []
                    for row in (rows or []):
                        run_id, triggered_at_val, score = row[0], row[1], row[2]
                        labels.append(triggered_at_val[:19] if triggered_at_val else str(run_id))
                        scores.append(float(score) if score is not None else 0)
                    if rows:
                        _progress_df = pd.DataFrame({"Run time": labels, "Score (%)": scores})
                        _progress_df["Score (%)"] = _progress_df["Score (%)"].astype(float)
                        _n_runs = len(rows)
                        _latest = scores[-1] if scores else 0
                        _p1, _p2, _p3 = st.columns(3)
                        with _p1:
                            st.metric("Runs", _n_runs)
                        with _p2:
                            st.metric("Latest score", f"{_latest:.1f}%")
                        with _p3:
                            st.metric("Trend", f"{(scores[-1] - scores[0]):.1f}%" if len(scores) > 1 else "—", delta="vs first run" if len(scores) > 1 else None, delta_color="off")
                        st.line_chart(_progress_df.set_index("Run time"), y="Score (%)")
                        st.caption("Overall WAF score (average of 4 pillars) per Reload Data run.")
                    else:
                        st.info("No completed runs yet. Run Reload Data to populate history.")
                else:
                    st.info("No run history with scores. Run Reload Data and ensure waf_total_percentage_across_pillars_hist exists.")
            except Exception as e:
                st.error(f"Failed to load progress: {e}")
    st.stop()

if st.session_state.waf_page == "recommendations":
    st.title("📋 WAF Recommendations (Not Met)")
    st.markdown("Controls that did not meet threshold and their recommended actions.")
    st.markdown("---")
    if st.button("← Back to Dashboard", type="secondary"):
        st.session_state.waf_page = "dashboard"
        st.session_state._nav_by_user = True
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()
    if not WAREHOUSE_ID:
        st.warning("No warehouse configured (WAF_WAREHOUSE_ID). Run install and set app env vars.")
    else:
        _wc = _get_ws_client()
        if not _wc:
            st.error("Databricks SDK could not initialise.")
        else:
            try:
                from databricks.sdk.service.sql import StatementState
                _stmt = f"SELECT waf_id, pillar_name, principle, best_practice, score_percentage, control_threshold_pct, recommendation_if_not_met FROM `{_catalog}`.`{_schema}`.waf_recommendations_not_met ORDER BY pillar_name, waf_id"
                _r = _wc.statement_execution.execute_statement(
                    statement=_stmt,
                    warehouse_id=WAREHOUSE_ID,
                    wait_timeout="30s",
                )
                if _r.status and _r.status.state == StatementState.SUCCEEDED and _r.result and _r.result.data_array:
                    rows = _r.result.data_array
                    # Column names: manifest may be on result or on response; SDK versions vary
                    cols = None
                    for _src in (_r.result, _r):
                        if getattr(_src, "manifest", None) and getattr(_src.manifest, "schema", None) and getattr(_src.manifest.schema, "columns", None):
                            cols = [c.name for c in (_src.manifest.schema.columns or [])]
                            break
                    if not cols and rows:
                        _n = len(rows[0]) if rows else 0
                        _known = ["waf_id", "pillar_name", "principle", "best_practice", "score_percentage", "control_threshold_pct", "recommendation_if_not_met"]
                        cols = _known if _n == len(_known) else [f"col{i}" for i in range(_n)]
                    import pandas as pd
                    _df = pd.DataFrame(rows, columns=cols) if cols else pd.DataFrame(rows)

                    # ---- Beautiful HTML: one card per waf_id with recommendation text ----
                    import html as _html_mod
                    def _html_esc(s):
                        return _html_mod.escape(str(s)) if s is not None else ""
                    def _strip_platform(s):
                        if s is None:
                            return ""
                        return str(s).replace("AWS | Azure | GCP", "").strip()

                    _card_css = """
                    <style>
                    .waf-rec-card { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-left: 4px solid #0ea5e9; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
                    .waf-rec-card .waf-id { font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 0.25rem; }
                    .waf-rec-card .waf-meta { font-size: 0.85rem; color: #64748b; margin-bottom: 0.5rem; }
                    .waf-rec-card .waf-rec-label { font-size: 0.75rem; font-weight: 600; color: #0ea5e9; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.75rem; margin-bottom: 0.35rem; }
                    .waf-rec-card .waf-rec-text { font-size: 0.95rem; line-height: 1.55; color: #334155; white-space: pre-wrap; }
                    .waf-rec-score { display: inline-block; background: #e2e8f0; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-left: 0.5rem; }
                    </style>
                    """
                    _html_parts = [_card_css]
                    for _, row in _df.iterrows():
                        waf_id = _html_esc((str(row.get("waf_id", "")).strip() or "—"))
                        pillar = _html_esc(_strip_platform(row.get("pillar_name")) or "—")
                        principle = _html_esc(_strip_platform(row.get("principle")) or "—")
                        best_practice = _html_esc(_strip_platform(row.get("best_practice")) or "—")
                        rec = _html_esc(_strip_platform(row.get("recommendation_if_not_met")) or "(No recommendation)")
                        score = row.get("score_percentage")
                        thresh = row.get("control_threshold_pct")
                        score_str = ""
                        if score is not None or thresh is not None:
                            score_str = f' <span class="waf-rec-score">Score: {score}% / Threshold: {thresh}%</span>' if thresh is not None else f' <span class="waf-rec-score">Score: {score}%</span>'
                        _html_parts.append(
                            f'<div class="waf-rec-card">'
                            f'<div class="waf-id">{waf_id}{score_str}</div>'
                            f'<div class="waf-meta"><strong>Pillar:</strong> {pillar} &nbsp;|&nbsp; <strong>Principle:</strong> {principle}</div>'
                            f'<div class="waf-meta"><strong>Best practice:</strong> {best_practice}</div>'
                            f'<div class="waf-rec-label">Recommendations</div>'
                            f'<div class="waf-rec-text">{rec}</div>'
                            f'</div>'
                        )
                    st.markdown("\n".join(_html_parts), unsafe_allow_html=True)

                    # Export to PDF: one-click download, dynamic filename, pillar/principle/score in body
                    def _pdf_sanitize(s):
                        if not s:
                            return ""
                        s = str(s)
                        replacements = (
                            ("—", "-"), ("–", "-"), ("\"", '"'), ("\"", '"'), ("'", "'"), ("'", "'"),
                            ("…", "..."), ("\u00a0", " "), ("\u2014", "-"), ("\u2013", "-"),
                        )
                        for a, b in replacements:
                            s = s.replace(a, b)
                        return "".join(c for c in s if ord(c) < 256 or c in " \n\t")

                    def _build_recommendations_pdf(pdf_date):
                        from fpdf import FPDF
                        pdf = FPDF()
                        pdf.set_auto_page_break(True, margin=12)
                        pdf.set_margins(14, 12, 14)
                        pdf.add_page()
                        # Title
                        pdf.set_font("Helvetica", "B", 16)
                        pdf.cell(0, 10, _pdf_sanitize("WAF Assessment - Recommendations (Not Met)"), ln=True)
                        pdf.set_font("Helvetica", "", 9)
                        pdf.cell(0, 6, _pdf_sanitize(f"Workspace: {WORKSPACE_ID}  |  Date: {pdf_date}  |  Catalog: {_catalog}.{_schema}"), ln=True)
                        pdf.ln(2)
                        pdf.set_draw_color(200, 200, 200)
                        pdf.line(14, pdf.get_y(), pdf.w - 14, pdf.get_y())
                        pdf.ln(6)
                        for _, row in _df.iterrows():
                            waf_id = _pdf_sanitize(str(row.get("waf_id", "")))
                            pillar = _pdf_sanitize(_strip_platform(row.get("pillar_name", "")))
                            principle = _pdf_sanitize(_strip_platform(row.get("principle", "")))
                            score = row.get("score_percentage")
                            thresh = row.get("control_threshold_pct")
                            score_txt = "N/A"
                            if score is not None and thresh is not None:
                                score_txt = f"{score}% / {thresh}%"
                            elif score is not None:
                                score_txt = f"{score}%"
                            rec = _pdf_sanitize(_strip_platform(row.get("recommendation_if_not_met", "")))[:2000]
                            # Control header
                            pdf.set_font("Helvetica", "B", 11)
                            pdf.set_fill_color(240, 248, 255)
                            pdf.cell(0, 7, f"  {waf_id}", ln=True, fill=True)
                            pdf.set_font("Helvetica", "", 9)
                            pdf.cell(0, 5, _pdf_sanitize(f"Pillar: {pillar}"), ln=True)
                            pdf.cell(0, 5, _pdf_sanitize(f"Principle: {principle}"), ln=True)
                            pdf.cell(0, 5, _pdf_sanitize(f"Current score / Threshold: {score_txt}"), ln=True)
                            pdf.set_font("Helvetica", "B", 9)
                            pdf.cell(0, 5, "Recommendations:", ln=True)
                            pdf.set_font("Helvetica", "", 9)
                            pdf.multi_cell(0, 5, rec or "(No recommendation)")
                            pdf.ln(4)
                        out = pdf.output()
                        return bytes(out) if not isinstance(out, bytes) else out

                    from datetime import datetime as _dt
                    _pdf_date = _dt.utcnow().strftime("%Y-%m-%d")
                    _pdf_bytes = _build_recommendations_pdf(_pdf_date)
                    _pdf_filename = f"WAF_ASSESSMENT_Recommendation_{WORKSPACE_ID}_{_pdf_date}.pdf"
                    st.download_button("Export to PDF", data=_pdf_bytes, file_name=_pdf_filename, mime="application/pdf", type="primary", use_container_width=False, key="pdf_export")
                else:
                    st.info("No rows returned. Run Reload Data and ensure the view `waf_recommendations_not_met` exists.")
            except Exception as e:
                st.error(f"Failed to load recommendations: {e}")
    st.stop()

# ── Genie Readiness page ─────────────────────────────────────────────────────
if st.session_state.waf_page == "genie_readiness":
    st.title("🔮 Genie Readiness")
    st.markdown(
        "Check whether this workspace meets every criterion to deploy **Databricks Genie** for end users. "
        "Checks run **live** — make a change and click **Re-check** to see the updated status."
    )
    st.markdown("---")

    _col_back, _col_recheck, _col_ts = st.columns([2, 1, 3])
    with _col_back:
        if st.button("← Back to Dashboard", type="secondary", key="back_genie"):
            st.session_state.waf_page = "dashboard"
            st.session_state._nav_by_user = True
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

    if not WAREHOUSE_ID:
        st.warning("No warehouse configured (WAF_WAREHOUSE_ID). Re-run install.ipynb.")
        st.stop()

    _wc = _get_ws_client()
    if not _wc:
        st.error("Databricks SDK could not initialise. Check app configuration.")
        st.stop()

    # Session-state cache (TTL = 5 min; cleared by Re-check button)
    _CACHE_KEY    = "genie_readiness_data"
    _CACHE_TS_KEY = "genie_readiness_ts"
    _CACHE_TTL    = 300

    with _col_recheck:
        if st.button("🔄 Re-check", type="primary"):
            st.session_state.pop(_CACHE_KEY, None)
            st.session_state.pop(_CACHE_TS_KEY, None)
            st.rerun()

    _now       = _time.time()
    _cached    = st.session_state.get(_CACHE_KEY)
    _cached_at = st.session_state.get(_CACHE_TS_KEY, 0)

    if _cached is None or (_now - _cached_at) > _CACHE_TTL:
        with st.spinner("Running live Genie Readiness checks against system tables…"):
            _gr = _run_genie_readiness_checks(_wc, WAREHOUSE_ID)
            _gr["unified_login"] = _check_unified_login(_wc)
        st.session_state[_CACHE_KEY]    = _gr
        st.session_state[_CACHE_TS_KEY] = _time.time()
        _cached = _gr

    r = _cached
    with _col_ts:
        # Use session_state for freshest timestamp — _cached_at is a snapshot from
        # before the if-block runs, so it stays 0 on first load if we use the local var.
        _age = int(_now - st.session_state.get(_CACHE_TS_KEY, _now))
        st.caption(f"Checked {_age}s ago — refreshes every 5 min or on Re-check")

    # ── Readiness badge ──────────────────────────────────────────────────────
    tier, _core_flags, _genie_flags = _compute_readiness_tier(r)

    _BADGE = {
        "green":  ("#1a7f37", "#dafbe1", "🟢 Genie Ready",
                   "All criteria met — this workspace is ready for Genie deployment."),
        "yellow": ("#9a6700", "#fff8c5", "🟡 Has Pre-Reqs",
                   "Core requirements met. Complete the Genie-Ready criteria below to unlock 🟢."),
        "red":    ("#cf222e", "#ffebe9", "🔴 Not Ready",
                   "Core requirements are missing. Address the ❌ items below first."),
    }
    _bc, _bg, _bl, _bd = _BADGE[tier]
    st.markdown(
        f'<div style="padding:1rem 1.5rem;border-radius:0.5rem;background:{_bg};'
        f'border-left:5px solid {_bc};margin-bottom:1rem;">'
        f'<div style="font-size:1.25rem;font-weight:700;color:{_bc};">{_bl}</div>'
        f'<div style="color:{_bc};margin-top:0.25rem;">{_bd}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Helper: render one criterion row ────────────────────────────────────
    # passed: True = ✅ confirmed, None = ⚠️ indeterminate, False = ❌ not met
    def _crit(passed, label, detail, note=None, doc_url=None):
        if passed is True:
            icon = "✅"
        elif passed is None:
            icon = "⚠️"
        else:
            icon = "❌"
        _c1, _c2 = st.columns([5, 5])
        with _c1:
            st.markdown(f"**{icon} {label}**")
            if note:
                st.caption(note)
        with _c2:
            st.markdown(detail)
            if passed is not True and doc_url:
                st.markdown(f"[→ How to enable]({doc_url})")

    # ── SP audit-access banner ───────────────────────────────────────────────
    # All identity checks read system.access.audit and system.query.history.
    # Databricks row-level security means a Service Principal without an explicit
    # GRANT can only see its OWN events — returning 0 for everything, indistinguishable
    # from "not configured".  Show ⚠️ rather than ❌ for any check that returned 0.
    _audit_all_zero = (
        not r.get("aim_configured") and not r.get("scim_active")
        and not r.get("federated_login") and not r.get("group_cloning_active")
        and (r.get("sql_only_users") or 0) == 0
    )
    _has_confirmed_data = (r.get("uc_count") or 0) > 0 or r.get("plan_tier") not in (None, "Unknown")
    if _audit_all_zero and _has_confirmed_data:
        st.warning(
            "⚠️ **Identity checks show ⚠️ because the WAF Service Principal "
            "may have row-filtered access to `system.access.audit`.** "
            "Without an explicit `GRANT SELECT ON SCHEMA system.access`, "
            "the SP only sees its own events — all identity checks return 0. "
            "Ask your metastore admin to run:\n\n"
            "```sql\n"
            "GRANT SELECT ON SCHEMA system.access TO `<sp-application-id>`;\n"
            "GRANT SELECT ON SCHEMA system.query TO `<sp-application-id>`;\n"
            "```\n\n"
            "After granting, click **Re-check**. "
            "The SP application ID is shown in the Databricks App details page."
        )

    # ── Core Requirements ────────────────────────────────────────────────────
    st.subheader("Core Requirements")
    st.caption("All four must be ✅ or ⚠️ to reach 🟡 Has Pre-Reqs")

    has_uc      = (r.get("uc_count") or 0) > 0
    has_premium = r.get("plan_tier", "Unknown") in ("Premium", "Enterprise")

    # Provisioning: True=confirmed, None=indeterminate (account-level SCIM / RLS)
    _scim_det = r.get("scim_users_detected")   # True | None
    _prov_confirmed = (
        r.get("aim_configured", False) or r.get("scim_active", False) or _scim_det is True
    )
    _prov_tristate = True if _prov_confirmed else None   # never ❌ for provisioning

    # Federated login: True=confirmed, None=indeterminate (audit RLS or genuine absence)
    _fed_tristate = True if r.get("federated_login") else None

    _crit(
        has_uc,
        "Unity Catalog",
        f"{r.get('uc_count', 0)} UC catalog(s) visible" if has_uc
            else "Not detected — only hive_metastore found",
        "Required for all Genie features and data access control",
        "https://docs.databricks.com/aws/en/data-governance/unity-catalog/enable-workspaces.html",
    )

    _plan = r.get("plan_tier", "Unknown")
    _plan_detail = (
        f"**{_plan}** plan detected via billing SKU" if _plan not in ("Unknown", None)
        else "Could not determine — `system.billing.usage` may not be accessible"
    )
    _crit(
        has_premium,
        "Premium or Enterprise Plan",
        _plan_detail,
        "Genie requires a Premium or Enterprise tier workspace",
        "https://www.databricks.com/product/pricing",
    )

    _prov_parts = []
    if r.get("aim_configured"):
        _last = str(r.get("last_aim_event", ""))[:10]
        _prov_parts.append(f"AIM configured (last event: {_last})")
    if r.get("scim_active"):
        _last = str(r.get("last_scim_event", ""))[:10]
        _prov_parts.append(f"SCIM active via audit log (last event: {_last})")
    if _scim_det is True:
        _prov_parts.append(r.get("scim_users_detail", "SCIM-managed users/groups detected"))
    if _prov_parts:
        _prov_detail = " · ".join(_prov_parts)
    elif _scim_det is None:
        _scim_msg = r.get("scim_users_detail", "")
        _prov_detail = (
            "No AIM/SCIM audit events in last 30 days (SP may need GRANT on system.access). "
            + (_scim_msg if _scim_msg else "Verify SCIM status in Admin Console → Identity & Access.")
        )
    else:
        _prov_detail = (
            "No provisioning evidence: no AIM/SCIM audit events in last 30 days "
            "and workspace has no users"
        )
    _crit(
        _prov_tristate,
        "Identity Provisioning (AIM / SCIM)",
        _prov_detail,
        "Detected via: (1) aimControlPolicy/SCIM audit events in system.access.audit, "
        "(2) users/groups with externalId (workspace-level SCIM only). "
        "Note: account-level SCIM (accounts.cloud.databricks.com) cannot be detected "
        "from the workspace API — verify in Admin Console if ⚠️ shows.",
        "https://docs.databricks.com/aws/en/admin/users-groups/scim/",
    )

    _idp = r.get("idp_type", "Not detected")
    _fed_detail = (
        f"**{_idp}** browser SSO detected (last 30 days)" if r.get("federated_login")
        else (
            "No browser-based SSO events visible — either not configured or SP needs "
            "GRANT on system.access.audit. "
            "Verify in Admin Console → Identity & Access → Identity Federation."
        )
    )
    _crit(
        _fed_tristate,
        "Federated Login / SSO Active",
        _fed_detail,
        "Detected from browser login events (aadBrowserLogin / samlLogin / oidcBrowserLogin) "
        "in system.access.audit. Token-based auth (PAT, OAuth M2M) does not satisfy this check.",
        "https://docs.databricks.com/aws/en/admin/users-groups/index.html#enable-identity-federation",
    )

    st.markdown("---")

    # ── Genie-Ready Criteria ────────────────────────────────────────────────
    st.subheader("Genie-Ready Criteria")
    st.caption("Required to reach 🟢 Genie Ready (in addition to Core Requirements above)")

    _sql_count = r.get("sql_only_users") or 0
    # ⚠️ when 0: could be SP audit RLS, not necessarily "no SQL-only users"
    _sql_tristate = True if _sql_count > 0 else None
    _crit(
        _sql_tristate,
        "Consumer / SQL-Only Users",
        f"**{_sql_count}** users with warehouse-only activity in last 30 days" if _sql_count > 0
            else (
                "0 returned — either all active users also use clusters, "
                "or SP needs GRANT on system.query.history to see warehouse activity"
            ),
        "Approximate: users active on SQL warehouses but not on clusters. "
        "True entitlement (databricks-sql-access) is managed in your IdP/SCIM settings.",
        "https://docs.databricks.com/aws/en/admin/users-groups/index.html",
    )

    _grp_count = r.get("synced_group_count") or 0
    _grp_tristate = True if r.get("group_cloning_active") else None
    _crit(
        _grp_tristate,
        "Group Cloning / IdP Group Sync",
        f"**{_grp_count}** group(s) synced from IdP in last 30 days" if r.get("group_cloning_active")
            else (
                "No IdP-synced group events visible — either not configured "
                "or SP needs GRANT on system.access.audit"
            ),
        "Groups should be provisioned from Entra/Okta so end-user Genie access is centrally managed",
        "https://docs.databricks.com/aws/en/admin/users-groups/scim/",
    )

    # Unified Login — optional, AWS only
    st.markdown("**Optional (AWS only)**")
    _ul = r.get("unified_login")
    if _ul is True:
        st.success("✅ **Unified Login**: Enabled — seamless cross-workspace SSO is active")
    elif _ul is False:
        st.warning(
            "⚠️ **Unified Login**: Disabled — consider enabling for seamless "
            "single sign-on across all workspaces in this account. "
            "[Docs →](https://docs.databricks.com/aws/en/admin/account-settings/)"
        )
    else:
        st.info(
            "ℹ️ **Unified Login**: Status could not be determined — reading this setting "
            "requires workspace admin privileges. "
            "[Check manually in Admin Console →](https://accounts.cloud.databricks.com)"
        )

    # Surface any query errors for transparency
    _errs = {k: v for k, v in r.items() if k.startswith("_err_")}
    if _errs:
        with st.expander("⚠️ Some checks could not run (click to expand)"):
            for _ek, _ev in _errs.items():
                st.caption(f"`{_ek.replace('_err_','')}`: {_ev}")
            st.caption(
                "This is usually caused by the service principal lacking SELECT on a system table. "
                "Re-run install.ipynb Cell 10 to re-grant permissions."
            )

    st.markdown("---")

    # ── Genie Usage ────────────────────────────────────────────────────────
    st.subheader("📊 Genie Usage — Last 30 Days")
    _mau  = r.get("genie_mau") or 0
    _msgs = r.get("genie_messages") or 0
    _l7   = r.get("msgs_last_7d") or 0
    _p7   = r.get("msgs_prev_7d") or 0

    _gu1, _gu2, _gu3 = st.columns(3)
    with _gu1:
        st.metric("Monthly Active Users", _mau,
                  help="Unique users who sent a message in a Genie conversation (last 30 days)")
    with _gu2:
        st.metric("Total Messages", _msgs,
                  help="Total Genie conversation messages in last 30 days")
    with _gu3:
        st.metric("Last 7 Days", _l7, delta=_l7 - _p7,
                  help="Messages in the last 7 days vs the previous 7 days")

    if _mau == 0:
        st.info(
            "💡 No Genie usage detected yet. Once Genie is enabled and users start "
            "conversations, activity will appear here automatically."
        )
    elif tier == "green":
        st.success(f"🎉 Genie is live with **{_mau} active user(s)** this month!")

    st.markdown("---")
    st.caption(
        "Checks use `system.access.audit`, `system.billing.usage`, `system.information_schema`, "
        "and `system.query.history`. "
        "Federated Login, AIM/SCIM, and Group Cloning signals are inferred from audit events — "
        "they indicate recent activity, not guaranteed current config state."
    )
    st.stop()

# ── End Genie Readiness page ──────────────────────────────────────────────────


# Dashboard page
st.title("🔍 WAF Assessment Dashboard")
st.markdown("**💡 Use the sidebar (←) to understand each metric and see recommended actions**")
st.markdown("---")

# Read-only display of catalog, schema, and latest run
_info_col1, _info_col2, _info_col3, _info_col4 = st.columns(4)
with _info_col1:
    st.metric("Data Catalog", _catalog)
with _info_col2:
    st.metric("Schema", _schema)
with _info_col3:
    if _run_info:
        _ts = _run_info.get("triggered_at", "—")
        st.metric("Last Reload", _ts[:16] if _ts else "—")  # trim seconds
    else:
        st.metric("Last Reload", "No data yet")
with _info_col4:
    if _run_info:
        _rid  = _run_info.get("run_id", "—")
        _ok   = _run_info.get("tables_succeeded", 0)
        _fail = _run_info.get("tables_failed", 0)
        _icon = "✅" if _run_info.get("status") == "success" else "⚠️"
        st.metric("Run", f"{_icon} #{_rid}", delta=f"{_ok}/{_ok+_fail} tables", delta_color="off")
    else:
        st.metric("Run", "—")

st.markdown("---")

# Reload Data button — triggers a Databricks Job via SDK (handles Apps OAuth M2M)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Reload Data", use_container_width=True, type="primary"):
        _catalog = os.environ.get("WAF_CATALOG", "useast1")

        if not JOB_ID:
            st.error("❌ Reload job not configured (WAF_JOB_ID missing). Re-run install.ipynb.")
        else:
            _wc = _get_ws_client()
            if not _wc:
                st.error("❌ Databricks SDK could not initialise. Check app configuration.")
            else:
                try:
                    _resp    = _wc.jobs.run_now(
                        job_id=int(JOB_ID),
                        notebook_params={"catalog": _catalog},
                    )
                    _run_id  = _resp.run_id
                    _run_url = f"{INSTANCE_URL}/?o={WORKSPACE_ID}#job/{JOB_ID}/run/{_run_id}"
                    _status_ph = st.empty()

                    # Poll until terminal state (up to 5 min)
                    _final_state = None
                    for _attempt in range(60):
                        _time.sleep(5)
                        _run     = _wc.jobs.runs.get(run_id=_run_id)
                        _lc      = _run.state.life_cycle_state.value if (
                            _run.state and _run.state.life_cycle_state) else ""
                        _status_ph.info(
                            f"⏳ Reload running ({(_attempt+1)*5}s elapsed) — "
                            f"[View job run ↗]({_run_url})"
                        )
                        if _lc == "TERMINATED":
                            _final_state = _run.state.result_state.value if (
                                _run.state and _run.state.result_state) else "UNKNOWN"
                            break

                    _status_ph.empty()
                    if _final_state == "SUCCESS":
                        st.success(f"✅ Reload complete — [View job run ↗]({_run_url})")
                    elif _final_state is None:
                        st.warning(f"⏳ Reload still running — [Check status ↗]({_run_url})")
                    else:
                        st.error(f"❌ Reload failed ({_final_state}) — [View job run ↗]({_run_url})")
                except Exception as _exc:
                    st.error(f"❌ Failed to trigger reload: {_exc}")

                st.rerun()

st.markdown("---")

# View Recommendations + View Progress + Genie Readiness
_rec_col1, _rec_col2, _rec_col3, _rec_col4, _rec_col5 = st.columns([0.5, 2, 2, 2, 0.5])
_link_style = (
    'display:inline-block;width:100%;padding:0.5rem 1rem;border-radius:0.5rem;'
    'background-color:#f0f2f6;color:#31333f;text-align:center;text-decoration:none;'
    'font-weight:500;border:1px solid rgba(49,51,63,0.2);box-sizing:border-box;'
)
with _rec_col2:
    st.markdown(
        f'<a href="?page=recommendations" target="_blank" rel="noopener noreferrer" style="{_link_style}">'
        '📋 View Recommendations (Not Met)</a>',
        unsafe_allow_html=True,
    )
with _rec_col3:
    st.markdown(
        f'<a href="?page=progress" target="_blank" rel="noopener noreferrer" style="{_link_style}">'
        '📈 View Progress</a>',
        unsafe_allow_html=True,
    )
with _rec_col4:
    st.markdown(
        f'<a href="?page=genie_readiness" target="_blank" rel="noopener noreferrer" style="{_link_style}">'
        '🔮 Genie Readiness</a>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# Dashboard access — Open Dashboard + Ask Genie (always show both; Genie URL from install)
_dashboard_direct_url = f"{INSTANCE_URL}/sql/dashboardsv3/{DASHBOARD_ID}"
_genie_url = GENIE_URL or f"{INSTANCE_URL}/genie?o={WORKSPACE_ID}"  # fallback to Genie home if not set by install
_btn_col1, _btn_col2, _btn_col3, _btn_col4 = st.columns([1, 2, 2, 1])
with _btn_col2:
    st.link_button(
        "↗ Open Dashboard in Databricks",
        _dashboard_direct_url,
        use_container_width=True,
    )
with _btn_col3:
    st.link_button(
        "🧞 Ask Genie",
        _genie_url,
        use_container_width=True,
    )
if not GENIE_URL:
    st.caption("💡 **Ask Genie**: Re-run install to link the WAF Genie room; the button above opens Genie.")

st.info(
    "**First time?** The dashboard below may show a Databricks login screen inside the iframe. "
    "Just click **Continue** — it will use your existing Databricks SSO session and sign you in "
    "automatically (no password needed). This is a one-time step per browser session. "
    "If you prefer, use the button above to open the dashboard directly in Databricks.",
    icon="ℹ️",
)

# Embed the dashboard using raw iframe (Databricks recommended format)
st.components.v1.html(
    f'<iframe src="{EMBED_URL}" width="100%" height="800" frameborder="0"></iframe>',
    height=810,
    scrolling=True,
)

st.markdown("---")
st.caption(f"Dashboard ID: {DASHBOARD_ID} | Workspace: {WORKSPACE_ID}")
