# Project State Snapshot
_Last updated: 2026-02-27_

**Canonical location**: `DONOTCHECKIN/tasks/state.md` (check here first; root `tasks/` may be a stale copy.)

---

## What We Are Building

A single-notebook installer (`install.ipynb`) that deploys a full **WAF Assessment Tool** on Databricks:

1. **Lakeview Dashboard** — real-time WAF scores across 4 pillars from `waf_cache` Delta tables; Genie AI Assistant tab embedded
2. **Databricks App** (Streamlit) — central hub: embedded dashboard, Reload Data, Recommendations (Not Met), View Progress, Ask Genie
3. **Genie Space** — AI chat pre-loaded with 15 WAF tables, instructions, 6 SQL examples; linked to dashboard via `uiSettings.overrideId`
4. **WAF Reload Job** — Spark notebook job that refreshes all `waf_cache` tables on demand

---

## Current Implementation Status

### Branch: `main` | Latest commit: `d69e920` — demo video added

### Validated: Full greenfield install confirmed working (2026-02-27)

| Component | Status | Detail |
|---|---|---|
| 145 waf_cache tables | ✅ | All tables in `{catalog}.waf_cache` |
| waf_recommendations_not_met view | ✅ | Populated after first reload |
| Dashboard deployed + published | ✅ | Warehouse attached, embed enabled |
| Genie space created + linked | ✅ | `uiSettings.genieSpace.overrideId` + `enablementMode: ENABLED` |
| WAF Reload job | ✅ | Created per install, initial reload triggered |
| App deployed (ACTIVE) | ✅ | app.yaml: WAF_CATALOG, WAF_JOB_ID, WAF_WAREHOUSE_ID, WAF_GENIE_URL |
| DASHBOARD_ID in app.py | ✅ | Patched in-memory at install time (Cell 8) |

---

## Architecture

```
install.ipynb (15 cells, run-all in Databricks workspace)
  Cell 1:  User sets catalog = "<your_catalog>" (only cell to edit)
  Cell 2:  Setup (api_url, token, ctx, notebook_dir) + greenfield UC/system-table checks
  Cell 3:  Ingest waf_controls_with_recommendations.csv → Delta
  Cell 4:  Create Genie Space (15 tables, instructions, 6 SQL examples)
  Cell 5:  Deploy Lakeview dashboard (embeds genie_space_id via uiSettings.overrideId)
  Cell 6:  Publish dashboard with SQL warehouse
  Cell 7:  Configure embedding domains (*.databricksapps.com)
  Cell 8:  Patch app.py in-memory (DASHBOARD_ID, INSTANCE_URL, WORKSPACE_ID)
  Cell 9:  Upload app files + create WAF Reload job + deploy Databricks App
  Cell 10: Grant SP permissions (waf_cache + system.*) + trigger initial reload
  Cell 11: Installation summary (per-step ✅/❌ + direct links + post-install access guide)
  Cell 14: Finalize Genie (SP permission, app.yaml WAF_GENIE_URL, redeploy)

streamlit-waf-automation/app.py
  - Embedded Lakeview dashboard (iframe, st.components.v1.html)
  - Reload Data → triggers WAF Reload job
  - View Recommendations (Not Met) → waf_recommendations_not_met view
  - View Progress → score trend chart across reload runs
  - Ask Genie → deep-link to Genie Space
  - WAF Guide sidebar
  - Navigation via _nav_by_user session flag + st.query_params.clear()

waf_cache tables in {CATALOG}.waf_cache:
  145 tables total:
  waf_controls_c/p/g/r                    (+ _hist)
  waf_principal_percentage_c/p/g/r        (+ _hist)
  waf_total_percentage_c/p/g/r            (+ _hist)
  waf_total_percentage_across_pillars     (+ _hist)
  waf_controls_with_recommendations       (Delta from CSV)
  waf_recommendations_not_met             (VIEW: join controls + CSV, filter Not Met)
  _run_log                                (auto-increment INT run_id)
  ~60+ individual metric tables           (+ _hist each)

docs/ (MkDocs Material site → GitHub Pages)
  index.md   — hero + Demo video + feature cards
  WAF2.0Demo.mp4 — 13MB demo video (converted from 54MB .mov, no audio, faststart)
  Live at: https://abhidatabricks.github.io/Databricks-WAF-Light-Tooling/
  GitHub Actions: .github/workflows/docs.yml → auto-deploys on push to main
```

---

## Key Technical Decisions

| Decision | Reason |
|---|---|
| `uiSettings.genieSpace.overrideId` + `enablementMode: ENABLED` | Reverse-engineered by diffing manually-linked dashboard JSON; `spaceId` and `PAGE_TYPE_GENIE` fail silently |
| `notebook_dir` from `ctx.notebookPath()` | `os.getcwd()` = `/databricks/driver/` when not in Repo; context path is always correct |
| Genie created before dashboard (Cell 4 before Cell 5) | `genie_space_id` must exist to embed in dashboard template at creation time |
| `nbformat_minor: 5` + cell `id` fields | Databricks notebook loader requires this format |
| Append model: `{table}_hist` + views | Preserves run history; dashboard unchanged (reads views) |
| INT auto-increment `run_id` | Human-readable; UUID was opaque |
| `subprocess.run(env=os.environ.copy())` | Databricks Apps sandboxing can block env var inheritance |
| Poll `compute_status.state == ACTIVE` before `/deployments` | Databricks compute init takes 2.5+ min on fresh app; retry-on-error was timing out |
| `st.components.v1.html()` with raw `<iframe>` | Matches Databricks recommended embed format (`frameborder="0"`) |
| Dashboard output path: `/Users/{user}/waf-dashboards` | Storing in repo's `dashboards/` caused timestamped files to accumulate and be picked up as templates |
| `_nav_by_user` session flag | Prevents `st.query_params` from re-overriding navigation on rerun |

---

## Key Files

| File | Purpose |
|---|---|
| `install.ipynb` | Main installer — 15 cells, run-all in Databricks |
| `streamlit-waf-automation/app.py` | Databricks App (Streamlit) — central hub |
| `streamlit-waf-automation/app.yaml` | App config — WAF_CATALOG, WAF_JOB_ID, WAF_WAREHOUSE_ID, WAF_GENIE_URL |
| `streamlit-waf-automation/waf_reload.py` | Notebook run as job to refresh waf_cache |
| `streamlit-waf-automation/dashboard_queries.yaml` | All WAF SQL queries (source of truth) |
| `streamlit-waf-automation/redeploy_app.py` | Redeploy app from local: `python redeploy_app.py <app_name> [path]` |
| `streamlit-waf-automation/genie` | Manual Genie setup instructions (paste into Genie Space UI if needed) |
| `dashboards/WAF_ASSESSMENTv1.7.1.lvdash.json` | Lakeview dashboard template |
| `docs/WAF2.0Demo.mp4` | Demo video (13MB MP4, no audio, web-optimised) |
| `DONOTCHECKIN/.creds` | Host, token, catalog, workspace_id for dev use |
| `DONOTCHECKIN/tasks/state.md` | THIS FILE — canonical project state |
| `DONOTCHECKIN/tasks/lessons.md` | Lessons learned (L0–L13) |
| `DONOTCHECKIN/tasks/decisions.md` | Decision log (D1–D10) |

---

## Credentials & Infrastructure

| Item | Value |
|---|---|
| Databricks host | `https://dbc-7545f99b-d884.cloud.databricks.com` |
| Workspace ID | `7474648347311915` |
| Catalog (dev) | `useast1` |
| SQL Warehouse | `1418991aeb011909` (Serverless Starter Warehouse) |
| App URL (dev) | `https://waf-automation-tool-7474648347311915.aws.databricksapps.com` |
| Databricks CLI | Configured — DEFAULT profile → host above |

## Active Constraints

- Install must run inside Databricks (uses Spark, dbutils, workspace APIs)
- Unity Catalog required; system tables must be enabled by workspace admin
- SQL Warehouse required — install raises if none found
- Databricks Apps feature must be enabled in the workspace
- Custom/dev code stays in `DONOTCHECKIN/` until tested and promoted to root
- Never add "co-authored by Claude" in commit messages
- Control view columns: `waf_controls_g` has `description`; c/p/r have `best_practice` — UNION uses `description AS best_practice` for g

---

## Completed (lifetime)

- [x] Fixed notebook format (nbformat_minor: 5, cell ids, stream output names)
- [x] Fixed path resolution: `os.getcwd()` → `notebook_dir` from `ctx.notebookPath()`
- [x] Fixed Genie linking: diff-based discovery of `uiSettings.genieSpace.overrideId` + `enablementMode: ENABLED`
- [x] Added greenfield checks (UC availability + system table accessibility)
- [x] Rewrote Cell 11 summary with per-step ✅/❌, all links, post-install access guide
- [x] Fixed "Back to Dashboard" navigation bug (`_nav_by_user` flag)
- [x] Append model with `_hist` tables + views (history preserved across reloads)
- [x] Auto-increment INT run_id (human-readable, replaces UUID)
- [x] Credentials: env vars only in app (no .creds fallback)
- [x] Dashboard output to `/Users/{user}/waf-dashboards` (not repo folder)
- [x] Poll compute ACTIVE before /deployments (not retry-on-error)
- [x] Added MkDocs Material docs site with GitHub Actions auto-deploy
- [x] Added WAF2.0Demo.mp4 to docs homepage and README (54MB .mov → 13MB .mp4)
- [x] Full greenfield install validated end-to-end (2026-02-27, ~4 min)

---

## Next Actions

1. Enable GitHub Pages if not already: Settings → Pages → Source: gh-pages branch
2. Share demo message + docs link with team
