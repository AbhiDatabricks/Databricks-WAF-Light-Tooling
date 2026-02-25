# Project State — Databricks WAF Light Tooling
_Last updated: 2026-02-25_

---

## Current Goal
Ship a polished, greenfield-safe single-notebook install for the WAF Assessment Tool on `persistdata`, then merge to `main`.

---

## Branch: `persistdata`
Not yet merged to `main`. All recent work is here.

---

## Architecture

```
install.ipynb (15 cells, run-all in Databricks workspace)
  Cell 1:  User sets catalog name
  Cell 2:  Setup (api_url, token, ctx, notebook_dir) + greenfield UC/system-table checks
  Cell 3:  Ingest waf_controls_with_recommendations.csv → Delta
  Cell 4:  Create Genie Space (15 tables, instructions, 6 SQL examples)
  Cell 5:  Deploy Lakeview dashboard (embeds genie_space_id via uiSettings.overrideId)
  Cell 6:  Publish dashboard with SQL warehouse
  Cell 7:  Configure embedding domains (*.databricksapps.com)
  Cell 8:  Patch app.py in-memory (DASHBOARD_ID, INSTANCE_URL, WORKSPACE_ID)
  Cell 9:  Upload app files + create WAF Reload job + deploy Databricks App
  Cell 10: Grant SP permissions (waf_cache + system.*) + trigger initial reload
  Cell 11: Installation summary (per-step ✅/❌ + direct links)
  Cell 14: Finalize Genie (SP permission, app.yaml WAF_GENIE_URL, redeploy)

streamlit-waf-automation/app.py
  - Embedded Lakeview dashboard (iframe)
  - Reload Data → triggers WAF Reload job
  - View Recommendations (Not Met) → waf_recommendations_not_met view
  - View Progress → score trend chart
  - Ask Genie → deep-link to Genie Space
  - WAF Guide sidebar

waf_cache tables in {CATALOG}.waf_cache:
  waf_controls_c/p/g/r, waf_principal_percentage_*, waf_total_percentage_*,
  waf_total_percentage_across_pillars, waf_controls_with_recommendations,
  waf_recommendations_not_met (VIEW)
```

---

## Key Technical Decisions

| Decision | Reason |
|---|---|
| `uiSettings.overrideId` to link Genie to dashboard | Reverse-engineered from manually-linked dashboard JSON; `spaceId` and `PAGE_TYPE_GENIE` both fail silently |
| `notebook_dir` from `ctx.notebookPath()` in Cell 2 | `os.getcwd()` = `/databricks/driver/` when not in a Repo; context path always correct |
| `nbformat_minor: 5` + cell `id` fields | Databricks notebook loader requires this; older format causes "Notebook failed to load" |
| Genie Space created before dashboard (Cell 4 before Cell 5) | `genie_space_id` must exist to embed in dashboard template at creation time |
| Initial reload triggered at end of install | Data loads in background so it's ready when user opens app |
| `deploy_api.ipynb` moved to `DONOTCHECKIN/` | Not needed for standard install |

---

## Completed This Session (2026-02-25)

- [x] Fixed notebook format (nbformat_minor, cell ids, stream output names)
- [x] Fixed path resolution: `os.getcwd()` → `notebook_dir` in Cells 4, 8, 9
- [x] Fixed Genie linking: `spaceId` → `overrideId` + `enablementMode: ENABLED`
- [x] Added greenfield checks (UC availability + system table accessibility)
- [x] Rewrote Cell 11 summary with per-step status and all links
- [x] Updated README with 4 screenshots and full feature docs
- [x] Moved `deploy_api.ipynb` to `DONOTCHECKIN/`

---

## Active Constraints

- Install must run inside Databricks (uses Spark, dbutils, workspace APIs)
- Unity Catalog required; system tables must be enabled by workspace admin
- SQL Warehouse required — install raises if none found
- Databricks Apps feature must be enabled in the workspace
- Custom/dev code stays in `DONOTCHECKIN/` until tested and promoted to root

---

## Next Actions

1. Merge `persistdata` → `main` (open PR)
2. Test full greenfield install on a new/clean workspace
3. Validate `waf_recommendations_not_met` view populates after first reload
