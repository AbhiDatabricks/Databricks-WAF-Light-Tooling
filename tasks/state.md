# Project State Snapshot

**→ Canonical copy: `DONOTCHECKIN/tasks/state.md`** — read and update that file first.

*Root copy last synced: 2025-02-19 (reconstructed from DONOTCHECKIN/tasks/ and conversation)*

---

## Current goal

- Keep the **WAF Assessment Tool** installable, runnable, and accurate.
- Recent focus: **recommendations** (CSV ingest, `waf_recommendations_not_met` view, app page + PDF export, Genie tables). That work is **done and committed** on `persistdata`.

---

## Active constraints

- **Custom/dev code** lives under `DONOTCHECKIN` until tested and moved to root (per Claude.md).
- **Catalog/schema**: All WAF cache lives in `{CATALOG}.waf_cache` (e.g. `useast1.waf_cache`). Install uses `CATALOG`; reload job uses widget `catalog`; app uses `WAF_CATALOG` env.
- **Genie**: Space has 15 tables (13 original + `waf_controls_with_recommendations`, `waf_recommendations_not_met`). Sending `instructions` in the Genie API can cause 500 — instructions are documented in `DONOTCHECKIN/waf_genie_instructions.md` for manual UI use.
- **Install** must run **inside Databricks** (notebook uses Spark, dbutils). Workspace may be **serverless-only** — job submit with `new_cluster` can fail; run install from the UI (open repo notebook, Run all).
- **Databricks CLI** and creds: `DONOTCHECKIN/.creds` (if present). Repo in workspace: e.g. `/Users/abhishekpratap.singh@databricks.com/Databricks-WAF-Light-Tooling-root`.

---

## Assumptions

- Source of truth for **dashboard queries** is `streamlit-waf-automation/dashboard_queries.yaml`; install builds the reload job from it.
- **Four pillars**: Governance (g), Cost (c), Performance (p), Reliability (r). Control views: `waf_controls_g/c/p/r`; Governance uses `description`, others use `best_practice`.
- **Recommendations**: Table `waf_controls_with_recommendations` is ingested from `streamlit-waf-automation/waf_controls_with_recommendations.csv` at install (Step 1b). View `waf_recommendations_not_met` is created in the reload job after the four control views.

---

## Decisions made

- **Recommendations view**: UNION the four control views (with `description AS best_practice` for g), JOIN to `waf_controls_with_recommendations` on `waf_id`, filter `threshold_met = 'Not Met'`.
- **App**: Second page via `st.session_state.waf_page`; recommendations page queries the view via SDK statement execution; PDF with fpdf2, bytes stored in session state then download button.
- **Genie**: Added two tables to `genie_tables` in install; full table list and column notes in `DONOTCHECKIN/waf_genie_instructions.md`.
- **Commits**: Do not mention "co-authored by Claude" (per Claude.md).

---

## Open risks

- **Install from CLI**: One-off job submit failed with "Only serverless compute is supported" when using `new_cluster`. Install is intended to be run manually from the notebook in the workspace.
- **DONOTCHECKIN** is gitignored — `waf_genie_instructions.md` and other dev artifacts are not in the repo; keep a copy or sync instructions elsewhere if needed for others.

---

## Next actions

1. **Run install** in Databricks UI (open `install.ipynb` from repo, set `catalog` in cell 2, Run all) if a full install/refresh is needed.
2. **Run Reload Data** from the app after install so control views and `waf_recommendations_not_met` are populated.
3. Optionally add **serverless job** definition for install if the workspace requires it for automation.
4. When making changes: update this state at checkpoints; log non-trivial decisions in `tasks/decisions.md`; capture lessons in `tasks/lessons.md`.

---

## Architecture (short)

- **install.ipynb**: Creates catalog/schema; ingests CSV to `waf_controls_with_recommendations`; deploys Lakeview dashboard, publishes it, deploys Streamlit app, creates reload job, grants SP permissions, creates Genie space with 15 tables.
- **Reload job** (notebook from `streamlit-waf-automation/waf_reload.py`): Runs queries from `dashboard_queries.yaml`, writes to `{catalog}.waf_cache.{table}_hist`, creates views for latest run; creates view `waf_recommendations_not_met`.
- **App** (`streamlit-waf-automation/app.py`): Dashboard page (metrics, Reload button, Open Dashboard, Ask Genie, iframe) + Recommendations page (query view, dataframe, Export to PDF, Back to Dashboard). Uses `WAF_CATALOG`, `WAF_WAREHOUSE_ID`, `WAF_JOB_ID`, `WAF_GENIE_URL` from env.
