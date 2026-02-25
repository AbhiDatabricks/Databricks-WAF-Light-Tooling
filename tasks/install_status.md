# WAF Install — What Works vs What Doesn't

Last tested: 2026-02-25 (run `wafauto-20260224-2343`, job `492475071425936`)

---

## ✅ WORKING (all steps pass end-to-end)

| Step | What | Detail |
|---|---|---|
| 1 | Config | `catalog = "useast1"` set in Cell 1 |
| 2 | Catalog + Schema | `useast1.waf_cache` created / verified |
| 2b | CSV ingest | `waf_controls_with_recommendations` table populated from CSV |
| 3-4 | Dashboard | Created from `*.lvdash.json` template, `{{catalog}}` substituted, name = `WAF_ASSESSMENTv1.7.1_<timestamp>` |
| 5 | Dashboard publish | Published with warehouse, `embed_credentials=True` |
| 6 | Embedding domains | PATCH sent to API — **see caveat below** |
| 7 | app.py patch | DASHBOARD_ID, INSTANCE_URL, WORKSPACE_ID substituted in memory |
| 8 | App upload | All files uploaded to `/Workspace/Users/{user}/wafauto-<ts>/` |
| 8 | WAF Reload Job | Created with `catalog` parameter, serverless env |
| 8 | app.yaml | All env vars injected: `WAF_CATALOG`, `WAF_JOB_ID`, `WAF_WAREHOUSE_ID`, `WAF_GENIE_URL` |
| 8 | App deploy | App created, compute ACTIVE, source deployed, app RUNNING |
| 9 | SP permissions | USE_CATALOG on catalog ✅ |
| 9 | SP schema grants | USE SCHEMA, CREATE TABLE, MODIFY, SELECT on `waf_cache` ✅ |
| 9 | SP system grants | USE SCHEMA + SELECT on `system.billing/compute/access/…` ✅ |
| 9 | Job permission | SP has `CAN_MANAGE_RUN` on reload job ✅ |
| 10 | Summary | Printed with all URLs |
| 13 | Genie Space | Created with 15 tables, 1 instruction block, 6 SQL queries, 6 sample questions ✅ |
| 13 | Genie link | `enablementMode: ENABLED` set on dashboard ✅ |
| 13 | Genie SP perm | SP has `CAN_USE` on Genie space ✅ |
| 13 | app.yaml update | `WAF_GENIE_URL` added and app redeployed ✅ |

---

## ⚠️ KNOWN LIMITATIONS (not bugs in the script)

### 1. `embedding_allowed_origins` — cannot be set per-dashboard via API
The install script PATCHes the dashboard with `{"embedding_allowed_origins": ["*.databricksapps.com"]}` but this field is NOT stored at the dashboard level — the API silently ignores it. The GET always returns `None`.

**Effect:** No functional issue because `*.databricksapps.com` is already whitelisted at workspace Admin → Security level. The iframe embedding works.

**If embedding breaks:** Go to workspace Admin Console → Security → Embedding → add `*.databricksapps.com`.

### 2. Genie `spaceId` not persisted in serialized_dashboard
The install script writes `{"genieSpace": {"isEnabled": True, "spaceId": ...}}` into the dashboard JSON, but the API does not expose `spaceId` in the response. The field `enablementMode: ENABLED` is what the API returns and it is correct — the Genie icon will appear on the dashboard.

**Effect:** No functional issue. When a user clicks the Genie icon on the dashboard, the WAF Genie space appears (linked by workspace context, not spaceId in the JSON).

### 3. Reload Job `catalog` base_parameter check
The reload job is created with `base_parameters: {catalog: <catalog>}` in the notebook task. The UC API for job inspection doesn't expose the base_parameters easily — but the job was verified to have the correct name `WAF Reload - useast1 (20260224_2343)`.

---

## 🐛 BUGS FIXED (in this session)

1. **Genie PATCH: `example_question_sqls must be sorted by id`** — the API rejects unsorted IDs. Fixed by sorting both `_sql_examples` and `_sample_qs` by their generated ID before including in the PATCH payload.

2. **Genie instructions too generic** — updated to match the working reference space instructions from `waf_genie_instructions.md`.

3. **PATCH status check too narrow** — changed from `in [200, 201]` to `200 <= status < 300`.

4. **`install_submit.json` used `new_cluster`** — this workspace is serverless-only; removed the cluster config.

---

## Quick re-run command

```bash
curl -s -X POST https://dbc-7545f99b-d884.cloud.databricks.com/api/2.0/jobs/runs/submit \
  -H "Authorization: Bearer $(grep token DONOTCHECKIN/.creds | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d @DONOTCHECKIN/install_submit.json
```
