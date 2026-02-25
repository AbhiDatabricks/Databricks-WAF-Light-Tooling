# Required Permissions

The person running `install.ipynb` needs the following permissions. These are checked at runtime — the installer will raise a clear error if something is missing.

---

## Permissions table

| Permission | Scope | Why it's needed |
|---|---|---|
| **Workspace Admin** _or_ **Apps Admin** | Workspace | Required to deploy Databricks Apps |
| **CREATE CATALOG** | Unity Catalog metastore | Only if the target catalog does not yet exist |
| **CREATE SCHEMA** | Target catalog | To create the `waf_cache` schema |
| **SELECT** on `system.*` | Unity Catalog | WAF queries read `system.billing`, `system.compute`, `system.access`, etc. |
| **Existing SQL Warehouse** | Workspace | Installer attaches it to publish the Lakeview dashboard |
| **Workspace files access** | Workspace | To upload app source files via the Workspace Files API |

---

## Checking system table access

Run this in a notebook or SQL editor before starting the install to confirm system tables are accessible:

```sql
SELECT * FROM system.billing.usage          LIMIT 1;
SELECT * FROM system.compute.clusters       LIMIT 1;
SELECT * FROM system.access.audit           LIMIT 1;
SELECT * FROM system.information_schema.tables LIMIT 1;
```

If any of these fail, contact your **workspace admin** to enable them in:

**Admin Console → Data → System Tables**

---

## Minimum vs recommended role

=== "Minimum"

    - Workspace user with **Apps Admin** privilege
    - **CREATE SCHEMA** on an existing catalog
    - SELECT on all `system.*` schemas

=== "Recommended (easiest)"

    - **Workspace Admin**
    - This covers all installer steps without any per-resource grants

---

## After install — what the app's Service Principal needs

The installer automatically grants the App's Service Principal (SP) the following. You don't need to do this manually:

```sql
-- waf_cache access
GRANT USE CATALOG ON CATALOG `<catalog>` TO `<sp>`;
GRANT USE SCHEMA  ON SCHEMA  `<catalog>`.`waf_cache` TO `<sp>`;
GRANT CREATE TABLE, MODIFY, SELECT ON SCHEMA `<catalog>`.`waf_cache` TO `<sp>`;

-- System table read access
GRANT USE SCHEMA ON SCHEMA system.billing       TO `<sp>`;
GRANT SELECT     ON ALL TABLES IN SCHEMA system.billing TO `<sp>`;
-- ... (repeated for compute, access, query, information_schema, mlflow)
```

!!! info
    If the initial reload job fails with a permissions error, re-run Cell 10 of `install.ipynb` to re-grant SP permissions, then trigger a new reload from the app.

---

## Next steps

- [Quick Start](quickstart.md) — run the installer
- [Grant Access to Users](grant-access.md) — share with your team after install
