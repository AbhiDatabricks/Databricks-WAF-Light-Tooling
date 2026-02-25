# Quick Start

Get WAF assessments running in your Databricks workspace in about 10 minutes.

---

## Prerequisites

Before you begin, verify:

- [ ] Your workspace has **Unity Catalog enabled**
- [ ] System tables are enabled (`system.billing`, `system.compute`, `system.access`, `system.information_schema`)
- [ ] At least one **SQL Warehouse** exists and is running
- [ ] **Databricks Apps** is enabled in the workspace
- [ ] You have the [required permissions](permissions.md)

!!! tip "Greenfield workspace?"
    The installer checks system table availability at startup and prints a clear warning if any are missing — it will not fail silently. Enable system tables in **Admin Console → Data → System Tables** before running.

---

## Step 1 — Add the repo to Databricks

1. Open your Databricks workspace
2. Navigate to **Workspace → Repos → Add Repo**
3. Paste the repo URL:

    ```
    https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling.git
    ```

4. Select branch: **`main`**
5. Click **Create Repo**

---

## Step 2 — Open and configure `install.ipynb`

1. In the Repos browser, open **`install.ipynb`**
2. Find **Cell 1** (the only cell you need to edit):

    ```python
    catalog = "<<Please enter waf catalog>>"
    ```

3. Replace the placeholder with your target Unity Catalog name:

    ```python
    catalog = "main"           # or "platform_shared", "my_catalog", etc.
    ```

!!! warning "Catalog must exist or be creatable"
    The installer creates the catalog if it does not exist, but requires `CREATE CATALOG` permission on the metastore. If the catalog already exists, `CREATE SCHEMA` on it is sufficient.

---

## Step 3 — Run All Cells

Click **Run All** (or use ++shift+ctrl+enter++ at each cell).

The installer runs **10 steps automatically**:

| Step | What happens |
|---|---|
| 1 | Env checks — Unity Catalog + system table availability |
| 2 | Catalog & `waf_cache` schema setup |
| 3 | Ingest WAF recommendations CSV into Delta |
| 4 | Create Genie Space (15 tables + AI instructions) |
| 5 | Deploy Lakeview dashboard (Genie AI tab embedded) |
| 6 | Publish dashboard with SQL warehouse |
| 7 | Configure embedding domain (`*.databricksapps.com`) |
| 8 | Patch and upload app files |
| 9 | Create WAF Reload Job + deploy Databricks App |
| 10 | Grant SP permissions + trigger initial data reload |

**Runtime:** ~5–8 minutes end-to-end.

---

## Step 4 — Review the installation summary

At the end of the notebook you'll see:

```
=================================================================
  INSTALLATION STATUS
=================================================================

  ✅  Dashboard created
        https://your-workspace.cloud.databricks.com/dashboardsv3/...
  ✅  Dashboard published
  ✅  Genie Space created & linked
        https://your-workspace.cloud.databricks.com/genie/spaces/...
  ✅  App deployed
        https://your-workspace-waf-automation-tool.databricksapps.com
  ✅  Reload job created
        https://your-workspace.cloud.databricks.com/?o=...#job/...
  ✅  Initial data reload triggered

=================================================================
  ✅  INSTALLATION COMPLETE — all steps succeeded!
=================================================================

  QUICK LINKS
  --------------------------------------------------
  Dashboard   →  https://...
  App         →  https://...
  Genie Space →  https://...
  Reload Job  →  https://...
```

!!! success "Data loads in the background"
    The first reload job runs automatically. WAF scores will be available in ~5–10 minutes. You can open the app immediately — the dashboard will populate as data arrives.

---

## Step 5 — Grant access to your team

The app, dashboard, and Genie Space are private by default. See [Grant Access to Users](grant-access.md) for the full sharing checklist.

---

## What's next?

- [Grant Access to Users](grant-access.md) — share with your team
- [Dashboard features](../features/dashboard.md) — understand the WAF pillars
- [Databricks App features](../features/app.md) — reload data, view recommendations
- [Genie AI Space](../features/genie.md) — ask WAF questions in plain English
