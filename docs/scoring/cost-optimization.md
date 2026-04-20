# Cost Optimization — Scoring Methodology

This pillar assesses how effectively your workspace controls and attributes costs through compute selection, serverless adoption, Photon usage, policies, tagging, and active FinOps practices.

## How scores are calculated

The WAF Reload job runs the control scoring query below against Databricks system tables and stores results in `waf_cache.waf_controls_c`. Each control receives a percentage score (0–100). If the score meets or exceeds the threshold, the control is marked **Met**.

## Control Scoring Query

The following SQL computes scores for all Cost Optimization controls. Run by the WAF Reload job and stored in `waf_cache.waf_controls_c`.

??? note "View SQL"
    ```sql
    WITH managed_usage AS (

      SELECT 

        TRY_DIVIDE(
          100.0 * SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END),
          SUM(CASE WHEN table_type IN ('MANAGED', 'EXTERNAL') THEN 1 ELSE 0 END)
        ) AS managed_percentage

      FROM system.information_schema.tables

      WHERE table_catalog != 'hive_metastore'

    ),

    serverless_usage AS (

      SELECT
        COUNT(*) as total_compute,
        SUM(CASE
              WHEN UPPER(sku_name) LIKE '%SERVERLESS%'
                OR UPPER(usage_type) LIKE '%SERVERLESS%'
              THEN 1 ELSE 0
            END) as serverless_count

      FROM system.billing.usage

      WHERE usage_date >= current_date() - INTERVAL 30 DAYS

        AND usage_type IN ('COMPUTE_TIME', 'GPU_TIME')

    ),

    photon_usage AS (

      SELECT 

        COUNT(*) as total_compute,

        SUM(CASE WHEN product_features.is_photon = true THEN 1 ELSE 0 END) as photon_compute

      FROM system.billing.usage

      WHERE usage_date >= current_date() - INTERVAL 30 DAYS

        AND usage_type LIKE '%COMPUTE%'

        AND billing_origin_product IN ('JOBS', 'INTERACTIVE', 'PIPELINES', 'ALL_PURPOSE')

    ),

    sql_warehouse_usage AS (

      SELECT
        COUNT(*) as total_compute,
        SUM(CASE WHEN compute.type = 'WAREHOUSE' THEN 1 ELSE 0 END) as sql_compute

      FROM system.query.history

      WHERE start_time >= current_timestamp() - INTERVAL 30 DAYS

    ),

    cluster_policies AS (

      SELECT
        COUNT(*) as total_clusters,
        SUM(CASE WHEN policy_id IS NOT NULL THEN 1 ELSE 0 END) as clusters_with_policy

      FROM (
        SELECT policy_id, delete_time,
               ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS rn
        FROM system.compute.clusters
      ) WHERE rn = 1 AND delete_time IS NULL

    ),

    cluster_tags AS (

      SELECT
        COUNT(*) as total_clusters,
        SUM(CASE WHEN size(map_keys(tags)) > 0 THEN 1 ELSE 0 END) as clusters_with_tags

      FROM (
        SELECT tags, delete_time,
               ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS rn
        FROM system.compute.clusters
        WHERE change_time >= current_date() - INTERVAL 30 DAYS
      ) WHERE rn = 1 AND delete_time IS NULL

    ),

    runtime_versions AS (

      SELECT
        COUNT(*) AS total_clusters,
        SUM(CASE WHEN TRY_CAST(split(regexp_replace(dbr_version, 'dlt:', ''), '[.]')[0] AS INT) >= 15 THEN 1 ELSE 0 END) AS up_to_date_clusters

      FROM (
        SELECT dbr_version, delete_time,
               ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS rn
        FROM system.compute.clusters
      ) WHERE rn = 1 AND delete_time IS NULL AND dbr_version IS NOT NULL

    ),

    billing_monitoring AS (

      SELECT
        COUNT(DISTINCT DATE(start_time)) AS active_days_last_30

      FROM system.query.history

      WHERE start_time >= current_timestamp() - INTERVAL 30 DAYS

        AND LOWER(statement_text) RLIKE 'system\.billing\.(usage|list_prices)'

    ),

    waf_status AS (

      SELECT
        waf_id,
        principle,
        best_practice,
        CASE 
        WHEN waf_id = 'CO-01-01' THEN (SELECT managed_percentage FROM managed_usage)
        WHEN waf_id = 'CO-01-03' THEN (
          SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
        )
        WHEN waf_id = 'CO-01-04' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (up_to_date_clusters * 100.0 / total_clusters) ELSE 0 END FROM runtime_versions
        )
        WHEN waf_id = 'CO-01-06' THEN (
          SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
        )
        WHEN waf_id = 'CO-01-09' THEN (
          SELECT CASE WHEN total_compute > 0 THEN (photon_compute * 100.0 / total_compute) ELSE 0 END FROM photon_usage
        )
        WHEN waf_id = 'CO-02-03' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
        )
        WHEN waf_id = 'CO-03-01' THEN (SELECT active_days_last_30 FROM billing_monitoring)
        WHEN waf_id = 'CO-03-02' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
        )
        ELSE 0
        END AS current_percentage,

        CASE 
        WHEN waf_id = 'CO-01-01' AND (SELECT managed_percentage FROM managed_usage) >= 80 THEN 'Yes'
        WHEN waf_id = 'CO-01-03' AND (
          SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
        ) >= 50 THEN 'Yes'
        WHEN waf_id = 'CO-01-04' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (up_to_date_clusters * 100.0 / total_clusters) ELSE 0 END FROM runtime_versions
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'CO-01-06' AND (
          SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
        ) >= 50 THEN 'Yes'
        WHEN waf_id = 'CO-01-09' AND (
          SELECT CASE WHEN total_compute > 0 THEN (photon_compute * 100.0 / total_compute) ELSE 0 END FROM photon_usage
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'CO-02-03' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'CO-03-01' AND (SELECT active_days_last_30 FROM billing_monitoring) >= 10 THEN 'Yes'
        WHEN waf_id = 'CO-03-02' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
        ) >= 80 THEN 'Yes'
        ELSE 'No'
        END AS implemented

      FROM (
        SELECT * FROM VALUES
        ('CO-01-01', 'Choose optimal resources', 'Prefer Managed table type over External tables'),
        ('CO-01-03', 'Choose optimal resources', 'Use SQL warehouse for SQL workloads'),
        ('CO-01-04', 'Choose optimal resources', 'Use up-to-date runtimes'),
        ('CO-01-06', 'Choose optimal resources', 'Use Serverless for your workloads'),
        ('CO-01-09', 'Choose optimal resources', 'Evaluate performance optimized query engines'),
        ('CO-02-03', 'Dynamically allocate resources', 'Use compute policies to control costs'),
        ('CO-03-01', 'Monitor and control cost', 'Monitor costs'),
        ('CO-03-02', 'Monitor and control cost', 'Tag clusters for cost attribution')
        AS waf(waf_id, principle, best_practice)
      )

    )

    SELECT
      waf_id,
      principle,
      best_practice,
      ROUND(current_percentage, 1) as score_percentage,
      CASE 
      WHEN waf_id = 'CO-01-01' THEN 80
      WHEN waf_id = 'CO-01-03' THEN 50
      WHEN waf_id = 'CO-01-04' THEN 80
      WHEN waf_id = 'CO-01-06' THEN 50
      WHEN waf_id = 'CO-01-09' THEN 80
      WHEN waf_id = 'CO-02-03' THEN 80
      WHEN waf_id = 'CO-03-01' THEN 10
      WHEN waf_id = 'CO-03-02' THEN 80
      END as threshold_percentage,
      CASE 
      WHEN implemented = 'Yes' THEN 'Met'
      ELSE 'Not Met'
      END as threshold_met,
      implemented

    FROM waf_status

    ORDER BY principle, waf_id;
    ```

---

## Controls

### CO-01-01 — Use performance optimized data formats

| Field | Value |
|---|---|
| Principle | Choose optimal resources |
| Threshold | 80% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of UC tables that are MANAGED vs EXTERNAL (managed percentage).

**Recommendation if Not Met**

Prefer managed tables where practical to reduce operational overhead and improve governance.

- For externally-managed locations, still use UC external locations + governed access.
- Convert legacy/external patterns selectively (start with shared 'gold' tables).
- Use system metadata to track progress: <https://docs.databricks.com/aws/en/admin/system-tables/>

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT 
        table_type,
        round(count(table_type)/(select count(*) from system.information_schema.tables) * 100) as percent_of_tables
    FROM system.information_schema.tables
    group by ALL
    having percent_of_tables > 0
    order by percent_of_tables desc
    ```

---

### CO-01-03 — Use SQL warehouse for SQL workloads

| Field | Value |
|---|---|
| Principle | Choose optimal resources |
| Threshold | 50% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of compute usage attributed to SQL warehouses (`sql_compute / total_compute` from `system.query.history`).

**Recommendation if Not Met**

Route SQL/BI workloads to SQL Warehouses (serverless where available) and keep notebook clusters for engineering/DS.

- Warehouse types and guidance: <https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types>
- Serverless SQL warehouse enablement: <https://docs.databricks.com/aws/en/admin/sql/serverless>
- Review queries in query history and migrate scheduled SQL jobs/dashboards to warehouses.

**Detail Query**

??? note "View SQL"
    ```sql
    -- SKU distribution between All-Purpose and SQL Warehouses
    select billing_origin_product, sum(usage_quantity) as dbu
    from system.billing.usage
    where billing_origin_product in ('SQL','ALL_PURPOSE')
      and usage_date >= current_date() - interval 30 days 
    group by billing_origin_product;
    ```

---

### CO-01-04 — Use up-to-date runtimes for your workloads

| Field | Value |
|---|---|
| Principle | Choose optimal resources |
| Threshold | 80% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of clusters using an up-to-date Databricks Runtime version (major version >= 15, regex-based) from `system.compute.clusters` at usage time.

**Recommendation if Not Met**

Enforce runtime currency (DBR upgrades) using compute policies and upgrade playbooks.

- Create/attach compute policies: <https://docs.databricks.com/aws/en/admin/clusters/policies>
- Policy attribute reference (to restrict/require DBR): <https://docs.databricks.com/aws/en/admin/clusters/policy-definition>
- Set an org standard (e.g., 'latest LTS or newer') and automate compliance reporting.

**Detail Query**

??? note "View SQL"
    ```sql
    select 
      regexp_extract(dbr_version, '^(\d+\.\d+)',1) as runtime,
      workspace_id,
      cluster_id,
      cluster_name
    from system.compute.clusters
    QUALIFY
      ROW_NUMBER() OVER (PARTITION BY account_id, workspace_id, cluster_id ORDER BY change_time DESC) = 1
      and delete_time is null
      and cluster_source not in('PIPELINE','PIPELINE_MAINTENANCE') 
      AND NOT contains(dbr_version, 'custom') 
    limit 100
    ```

---

### CO-01-06 — Use Serverless for your workloads

| Field | Value |
|---|---|
| Principle | Choose optimal resources |
| Threshold | 50% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of compute usage running on serverless SKUs (from `system.billing.usage` where `sku_name` contains `SERVERLESS`).

**Recommendation if Not Met**

Increase serverless adoption for eligible workloads to reduce idle costs and ops.

- Serverless SQL warehouse enablement: <https://docs.databricks.com/aws/en/admin/sql/serverless>
- For pipelines, consider serverless pipelines: <https://docs.databricks.com/aws/en/ldp/serverless>
- Start with dashboards/scheduled SQL + light ETL; keep classic compute for special networking/runtime needs.

**Detail Query**

??? note "View SQL"
    ```sql
    with serverless as (
        select sum(usage_quantity) as dbu
        from system.billing.usage u
        where contains(u.sku_name, 'SERVERLESS')
          and u.billing_origin_product in ('ALL_PURPOSE','SQL','JOBS','DLT','INTERACTIVE')
          and date_diff(day, u.usage_start_time, now()) < 28
    ),
    total as (
        select sum(usage_quantity) as dbu
        from system.billing.usage u
        where u.billing_origin_product in ('ALL_PURPOSE','SQL','JOBS','DLT','INTERACTIVE')
          and date_diff(day, u.usage_start_time, now()) < 28
    )
    select serverless.dbu * 100 / total.dbu as serverless_dbu_percent
    from serverless cross join total;
    ```

---

### CO-01-09 — Evaluate performance optimized query engines

| Field | Value |
|---|---|
| Principle | Choose optimal resources |
| Threshold | 80% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of compute usage with Photon enabled (from `system.billing.usage`/`product_features.is_photon` or SKU indicators).

**Recommendation if Not Met**

Enable Photon for eligible SQL/DataFrame workloads to improve price/performance.

- Photon overview and enablement: <https://docs.databricks.com/aws/en/compute/photon>
- Use compute policies to default Photon on (and allow opt-out only with justification).
- Validate with representative workloads; monitor DBU + runtime improvements.

**Detail Query**

??? note "View SQL"
    ```sql
    select ju.usage_metadata.cluster_id,
      c.cluster_name,
      ju.product_features.is_photon, 
      sum(ju.usage_quantity) as dbu 
    from system.billing.usage ju 
    join system.compute.clusters c on c.cluster_id = ju.usage_metadata.cluster_id
    where ju.usage_date BETWEEN current_date() - interval 90 days AND current_date()
      and ju.billing_origin_product in ('ALL_PURPOSE')
      and ju.product_features.is_serverless = false
    group by 1,2,3
    ```

---

### CO-02-03 — Use compute policies to control costs

| Field | Value |
|---|---|
| Principle | Dynamically allocate resources |
| Threshold | 80% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of clusters attached to a compute policy (`cluster_policy_id` present in `system.compute.clusters`).

**Recommendation if Not Met**

Expand compute policy coverage and make policies the default entry point for new compute.

- Create and manage compute policies: <https://docs.databricks.com/aws/en/admin/clusters/policies>
- Compute policy reference (attributes, tags, libraries): <https://docs.databricks.com/aws/en/admin/clusters/policy-definition>
- Provide policy families for common use cases (ETL, BI, DS) and lock down unsafe settings.

**Detail Query**

??? note "View SQL"
    ```sql
    select workspace_id,
      cluster_id,
      cluster_name,
      policy_id,
      case when policy_id is null then 'No' else 'Yes' end as cluster_policy
    from system.compute.clusters
    qualify
      ROW_NUMBER() OVER (PARTITION BY account_id, workspace_id, cluster_id ORDER BY change_time DESC) = 1
      and delete_time is null 
      and cluster_source in ('JOB')
    ```

---

### CO-03-01 — Monitor costs

| Field | Value |
|---|---|
| Principle | Monitor and control cost |
| Threshold | 10 distinct days (last 30) |
| waf_cache table | `waf_controls_c` |

**What it measures**

Number of distinct days in the last 30 days where queries referenced `system.billing.usage` or `system.billing.list_prices` (from `system.query.history`).

!!! note "Threshold interpretation"
    This is the only control scored in raw count rather than percentage. The threshold of 10 means billing tables should be queried on at least 10 distinct days per month, indicating an active FinOps practice.

**Recommendation if Not Met**

Operationalize FinOps using system billing tables, dashboards, and chargeback tags.

- Billable usage system table reference: <https://docs.databricks.com/aws/en/admin/system-tables/billing>
- Monitor costs using system tables: <https://docs.databricks.com/aws/en/admin/usage/system-tables>
- Set a weekly cadence: top spenders, unused warehouses, idle clusters, anomalous spikes.

**Detail Query**

??? note "View SQL"
    ```sql
    -- How often is system.billing.usage accessed in last 28 days?
    select
      event_date,
      count(*) as usage_read
    from system.access.audit
    where service_name = 'unityCatalog'
      and action_name = 'getTable'
      and request_params.full_name_arg = 'system.billing.usage'
      and user_identity.email != 'System-User'
      and (date_diff(day, event_date, current_date()) <= 90)
    group by event_date
    order by event_date;
    ```

---

### CO-03-02 — Tag clusters for cost attribution

| Field | Value |
|---|---|
| Principle | Monitor and control cost |
| Threshold | 80% |
| waf_cache table | `waf_controls_c` |

**What it measures**

% of clusters with user-defined tags set (`system.compute.clusters.tags` map not empty).

**Recommendation if Not Met**

Adopt a mandatory tagging standard (cost center, owner, env, project) and enforce it via policies.

- Using tags for usage attribution: <https://docs.databricks.com/aws/en/admin/account-settings/usage-detail-tags>
- Enforce tags via compute policies: <https://docs.databricks.com/aws/en/admin/clusters/policies>
- Make dashboards/chargeback depend on tags so teams feel the incentive to comply.

**Detail Query**

??? note "View SQL"
    ```sql
    select workspace_id, cluster_id, cluster_name, cluster_source
    from system.compute.clusters
    qualify
      ROW_NUMBER() OVER (PARTITION BY account_id, workspace_id, cluster_id ORDER BY change_time DESC) = 1
      and array_size(map_entries(tags)) = 0
      and delete_time is null 
      and cluster_source in ('API', 'UI', 'JOB')
    ```

---
