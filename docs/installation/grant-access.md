# Grant Access to Users

After installation, the app, dashboard, and Genie Space are private to the installer. Complete **all five steps** to give your team full access — missing any one will result in a broken experience.

!!! tip "URLs are printed at the end of `install.ipynb`"
    The installation summary shows the direct URL for each resource. Keep that output handy while following this guide.

---

## Summary checklist

| Step | Action | Where |
|---|---|---|
| **A** | Add users to the workspace | Admin Console → Users & Groups |
| **B** | Grant App: **CAN USE** | Apps → waf-automation-tool → Permissions |
| **C** | Grant Dashboard: **CAN VIEW** or **CAN EDIT** | Dashboard → Share |
| **D** | Grant Genie Space: **CAN USE** | Genie Space → Share |
| **E** | Run SQL GRANT on `waf_cache` schema | SQL Editor or notebook |

---

## Step A — Add users to the workspace

If the users are not yet members of the Databricks workspace:

1. Go to **Admin Console → Users & Groups**
2. Click **Add user** (individual) or **Add group** (SCIM/IdP-synced group)

Skip this step if users already have workspace access.

---

## Step B — Grant App access

1. In the workspace, go to **Apps** in the left sidebar
2. Find **`waf-automation-tool`** (name shown in install output)
3. Click the app → **Permissions**
4. Add user or group → select **CAN USE**

!!! warning
    Without this step, users will see a "Permission Denied" error when opening the app URL.

---

## Step C — Grant Dashboard access

1. Open the WAF Assessment Dashboard (URL from install output)
2. Click **Share** in the top-right corner
3. Add user or group and choose a permission level:
   - **CAN VIEW** — read-only, recommended for most users
   - **CAN EDIT** — co-author access

---

## Step D — Grant Genie Space access

1. Open the Genie Space (URL from install output)
2. Click **Share** in the top-right corner
3. Add user or group → select **CAN USE**

!!! warning
    Without this step, users will get a permission error when clicking **Ask Genie** in the app or opening the AI Assistant tab in the dashboard.

---

## Step E — Grant read access to WAF cache tables

Run the following SQL in a SQL Editor or notebook. Replace the placeholders:

```sql
-- Replace <catalog>        with your WAF catalog name (e.g. "main")
-- Replace <user_or_group>  with the user email or group display name
--                           exactly as it appears in Admin Console

GRANT USE CATALOG ON CATALOG `<catalog>`                           TO `<user_or_group>`;
GRANT USE SCHEMA  ON SCHEMA  `<catalog>`.`waf_cache`               TO `<user_or_group>`;
GRANT SELECT      ON ALL TABLES IN SCHEMA `<catalog>`.`waf_cache`  TO `<user_or_group>`;
```

!!! example "Example — granting access to a group"
    ```sql
    GRANT USE CATALOG ON CATALOG `main`                          TO `waf-users`;
    GRANT USE SCHEMA  ON SCHEMA  `main`.`waf_cache`              TO `waf-users`;
    GRANT SELECT      ON ALL TABLES IN SCHEMA `main`.`waf_cache` TO `waf-users`;
    ```

!!! note "Groups work best"
    Rather than granting per-user, create a group (e.g. `waf-users`) in Admin Console, add all users to it, and run the GRANT once for the group. New members automatically inherit access.

---

## Verifying access

Ask a user to open the App URL. A healthy session looks like:

1. App loads without permission errors
2. Dashboard renders with WAF scores
3. "View Recommendations" page shows data
4. "Ask Genie" opens the Genie Space without error

If any step fails, check the corresponding grant above.
