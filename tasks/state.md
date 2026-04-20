# Project State Snapshot
_Last updated: 2026-04-20_

**Canonical location**: `DONOTCHECKIN/tasks/state.md` (check here first; root `tasks/` may be a stale copy.)

---

## What We Are Building

A single-notebook installer (`install.ipynb`) that deploys a full **WAF Assessment Tool** on Databricks:

1. **Lakeview Dashboard** — WAF scores across 4 pillars, always reading from `waf_cache` Delta tables
2. **Databricks App** (Streamlit) — central hub: embedded dashboard, Reload Data, Recommendations (Not Met), View Progress, Ask Genie
3. **Genie Space** — AI chat pre-loaded with 15 WAF tables, instructions, 6 SQL examples; linked to dashboard
4. **WAF Reload Job** — Spark notebook job that refreshes all `waf_cache` tables on demand

---

## Architecture Invariant

**ALL queries (dashboard + app) must read from `{catalog}.waf_cache.*` — never directly from system tables.**
See `DONOTCHECKIN/CLAUDE.md` → Architecture Invariants for enforcement rules.

---

## Current Implementation Status

### Branch: `main` | Changes pending commit (6 files)

| Component | Status | Detail |
|---|---|---|
| Dashboard → waf_cache | ✅ | All 73 active datasets read from waf_cache; 10 ToDo placeholders unchanged |
| PE-02-05 scoring | ✅ | Binary score in waf_controls_p + CSV row added |
| PE-02-07 formula | ✅ | Cluster policy adoption % (was duplicate of PE-01-01) |
| Dashboard config via env vars | ✅ | WAF_INSTANCE_URL, WAF_DASHBOARD_ID, WAF_WORKSPACE_ID in app.yaml |
| _load_run_info timeout | ✅ | 10s → 50s (cold warehouse fix) |
| fevm app deployed | ✅ | wafauto-20260324-0756, all fixes live |
| fevm dashboard patched | ✅ | 01f1267860331f0a8d6cbde05503fc97, republished |
| Git push | ❌ | 6 files changed, not yet committed |

---

## install.ipynb Cell Map

```
Cell 1:  User sets catalog = "<your_catalog>"
Cell 2:  Setup (api_url, token, ctx, notebook_dir) + greenfield checks
Cell 3:  Ingest waf_controls_with_recommendations.csv → Delta
Cell 4:  Create Genie Space (⚠️ known issue: fails if waf_cache tables don't exist yet)
Cell 5:  Deploy Lakeview dashboard
Cell 6:  Publish dashboard with SQL warehouse
Cell 7:  Configure embedding domains
Cell 8:  Patch app.py in-memory (NO LONGER patches DASHBOARD_ID/INSTANCE_URL/WORKSPACE_ID — now env vars)
Cell 9:  Upload app files + build app.yaml (with WAF_INSTANCE_URL, WAF_DASHBOARD_ID, WAF_WORKSPACE_ID) + create WAF Reload job + deploy App
Cell 10: Grant SP permissions + trigger initial reload
Cell 11: Installation summary
Cell 14: Finalize Genie (SP permission, app.yaml WAF_GENIE_URL, redeploy)
```

---

## Key Technical Decisions

| Decision | Reason |
|---|---|
| `uiSettings.genieSpace.overrideId` + `enablementMode: ENABLED` | Reverse-engineered; `spaceId` and `PAGE_TYPE_GENIE` fail silently |
| `notebook_dir` from `ctx.notebookPath()` | `os.getcwd()` = `/databricks/driver/` when not in Repo |
| Dashboard config via env vars (not regex-patched into app.py) | Uploading local app.py clobbered workspace-specific values |
| `wait_timeout="50s"` in `_load_run_info()` | Cold warehouse takes 30–60s; 10s caused "No data yet" on fresh load |
| All dashboard datasets → waf_cache | Single source of truth; prevents score mismatch between dashboard and app |
| `{{catalog}}` placeholder in dashboard JSON | Replaced at install time via `raw.replace("{{catalog}}", CATALOG)` |
| Append model: `{table}_hist` + views pointing to latest run_id | Preserves history; dashboard/app always see latest snapshot |
| INT auto-increment `run_id` | Human-readable; UUID was opaque |
| `_nav_by_user` session flag | Prevents `st.query_params` from re-overriding page on rerun |

---

## Key Files

| File | Purpose |
|---|---|
| `install.ipynb` | Main installer — run-all in Databricks |
| `streamlit-waf-automation/app.py` | Databricks App (Streamlit) |
| `streamlit-waf-automation/app.yaml` | App config — WAF_CATALOG, WAF_JOB_ID, WAF_WAREHOUSE_ID, WAF_GENIE_URL, WAF_INSTANCE_URL, WAF_DASHBOARD_ID, WAF_WORKSPACE_ID |
| `streamlit-waf-automation/waf_reload.py` | Notebook job to refresh waf_cache |
| `streamlit-waf-automation/dashboard_queries.yaml` | All WAF SQL (source of truth for waf_reload.py) |
| `dashboards/WAF_ASSESSMENTv1.7.1.lvdash.json` | Lakeview dashboard template |
| `DONOTCHECKIN/CLAUDE.md` | Project guidelines + Architecture Invariants |
| `DONOTCHECKIN/tasks/state.md` | Canonical state (this file in DONOTCHECKIN is the real one) |
| `DONOTCHECKIN/tasks/lessons.md` | Lessons learned |

---

## Pending / Open Issues

1. **Git push** — 6 files changed, not committed yet
2. **install.ipynb — Genie creation timing** (Cell 4/Cell 14): Genie Space creation fails if waf_cache tables don't exist; tables only exist after first reload job runs (triggered in Cell 10). Known issue, not yet fixed.
3. **install.ipynb — SP grant error messages**: `GRANT USE CATALOG ON CATALOG system` and `system.billing` grants fail with PERMISSION_DENIED for non-metastore/account admins — error message should give clear manual-grant instructions instead of misleading green summary.
4. **PE-02-02 / PE-02-04 drill-down** (Albert feedback): only high-level guidance, no resource-level detail. By design for now.
