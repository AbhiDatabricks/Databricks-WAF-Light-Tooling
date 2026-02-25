# Troubleshooting

---

## Installation issues

### "Notebook failed to load" in Databricks

**Cause:** The notebook JSON is missing `nbformat_minor: 5`, cell `id` fields, or stream outputs missing the `name` field.

**Fix:** Pull the latest `main` branch — these issues were fixed. If you're on an older commit, update your Repo in Databricks.

---

### Job fails with "Workload failed" after ~60 seconds

**Cause:** File paths are resolved incorrectly. `os.getcwd()` returns `/databricks/driver/` when a notebook is uploaded directly (not inside a Repo), so dashboard/app files are not found.

**Fix:** This is fixed in `main`. The installer derives `notebook_dir` from `ctx.notebookPath()` in Cell 2 — this is always correct regardless of how the notebook is accessed.

---

### System table warnings at startup

```
⚠️ system.billing.usage — NOT accessible
```

**Cause:** System tables are not enabled in this workspace.

**Fix:**
1. Go to **Admin Console → Data → System Tables**
2. Enable the required system tables
3. Re-run `install.ipynb` from Cell 2 onwards
4. After install, trigger a reload from the app

WAF scores will be partial or zero until system tables are populated.

---

### "No SQL warehouse found"

**Cause:** No running SQL warehouse exists in the workspace.

**Fix:** Create or start a SQL warehouse in **SQL → SQL Warehouses** and re-run the install.

---

### Genie Space created but not appearing as AI Assistant tab

**Cause:** The dashboard was created before the Genie Space, or the linking API field was wrong.

**Fix:** Re-run Cell 5 (dashboard creation) after Cell 4 (Genie creation) to re-embed the Genie Space ID. The correct API field is `uiSettings.genieSpace.overrideId` with `enablementMode: "ENABLED"`.

---

## Embedding issues

### "Embedding dashboards is not available on this domain"

This error appears when workspace-level dashboard embedding is disabled.

**Step 1 — Enable workspace-level embedding (Admin required)**

1. Go to **Admin Console → Advanced**
2. Enable **"Allow AI/BI dashboard embedding"**
3. Save

**Step 2 — Confirm the domain allowlist**

1. Open the WAF dashboard
2. Click **Share → Embed dashboard**
3. Verify `*.databricksapps.com` is listed
4. If not, add it and save

The installer configures this via API, but the API call only takes effect after Step 1 is done.

---

## App issues

### "Back to Dashboard" button doesn't work / page reloads to same view

**Cause:** `st.query_params` was being read unconditionally on every rerun, overriding the session state.

**Fix:** This is fixed in `main`. Navigation now uses a `_nav_by_user` session state flag and calls `st.query_params.clear()` when navigating back.

---

### App shows permission error for some users

Check all five steps in [Grant Access to Users](installation/grant-access.md):

- [ ] User is in the workspace
- [ ] User has **CAN USE** on the app
- [ ] User has **CAN VIEW** on the dashboard
- [ ] User has **CAN USE** on the Genie Space
- [ ] SQL GRANT on `{catalog}.waf_cache` has been run

---

### Recommendations page is empty

**Cause 1:** The `waf_recommendations_not_met` view depends on `waf_controls_with_recommendations` (ingested from CSV in Cell 3) and the pillar control tables. If either is missing, the view returns empty.

**Fix:** Re-run Cell 3 of `install.ipynb`, then trigger a reload from the app.

**Cause 2:** No controls are below threshold — everything passes! The page only shows failing controls.

---

### WAF scores are all zero after install

**Cause:** The initial reload job is still running, or system tables haven't been populated yet.

**Fix:** Wait 5–10 minutes after install for the first reload to complete. Check the reload job status in Databricks Jobs. If the job failed, see the job run logs for the specific error.

---

## Getting help

- Open an issue on [GitHub](https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling/issues)
- Check the WAF Guide sidebar in the app for per-control documentation
