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

# View Recommendations + View Progress (open in new tab)
_rec_col1, _rec_col2, _rec_col3, _rec_col4 = st.columns([1, 2, 2, 1])
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
