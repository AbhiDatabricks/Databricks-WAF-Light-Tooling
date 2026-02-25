# Lessons Learned

**→ Canonical copy: `DONOTCHECKIN/tasks/lessons.md`** — read and update that file first.

*Root copy; full lessons (L0–L11) are in DONOTCHECKIN/tasks/lessons.md.*

---

## Project conventions

1. **DONOTCHECKIN**: Dev-only and sensitive files go under `DONOTCHECKIN/`; do not rely on them being in git (folder is gitignored).
2. **Catalog variable**: Install uses `CATALOG`; reload job uses widget `catalog`; app uses `WAF_CATALOG` env. Keep naming consistent when adding new references.
3. **Genie table names**: Install and docs use `waf_principal_percentage_*` and `waf_total_percentage_*`; Claude.md lists "waf_principal_c" etc. — the codebase uses the longer names.

---

## Implementation

4. **Control view columns**: `waf_controls_g` has `description`; `waf_controls_c`, `waf_controls_p`, `waf_controls_r` have `best_practice`. Any UNION of control views must use `description AS best_practice` for Governance.
5. **Streamlit + functions**: Define helpers (e.g. `_get_ws_client`, `_load_run_info`) **before** first use in the script; avoid defining them in the middle of the main flow.
6. **Install notebook**: Requires Spark/dbutils — runs only inside Databricks. For automation, use workspace UI "Run all" or a job that runs the notebook; some workspaces only allow serverless compute for jobs.

---

## Workflow

7. **Context refresh**: Reconstruct from `tasks/state.md` and `tasks/lessons.md`; summarize architecture, objectives, constraints, next step.
8. **Commits**: Never add "co-authored by Claude" in commit messages.

---

## To add here after corrections

- When the user corrects a bug or behavior: add a short entry above with the pattern and how to prevent it next time.
