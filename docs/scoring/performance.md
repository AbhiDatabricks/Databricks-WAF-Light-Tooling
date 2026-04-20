# Performance Efficiency — Scoring Methodology

This pillar assesses how well your workspace leverages serverless compute, parallel processing, native Spark operations, Photon, and hardware-appropriate configurations to achieve efficient workload performance.

## How scores are calculated

The WAF Reload job runs the control scoring query below against Databricks system tables and stores results in `waf_cache.waf_controls_p`. Each control receives a percentage score (0–100). If the score meets or exceeds the threshold, the control is marked **Met**.

## Control Scoring Query

The following SQL computes scores for all Performance Efficiency controls. Run by the WAF Reload job and stored in `waf_cache.waf_controls_p`.

!!! note "PE-02-05 and PE-02-07"
    This is the current (fixed) `waf_controls_p` query. It adds PE-02-05 (Python UDFs check) and updates PE-02-07 to measure cluster policy attachment for interactive clusters — replacing the earlier serverless-only proxy. The old query (`waf_controls_p_old`) is excluded.

??? note "View SQL"
    ```sql
    WITH serverless_usage AS (

      SELECT 

        COUNT(*) as total_compute,

        SUM(CASE WHEN usage_type LIKE '%SERVERLESS%' OR sku_name LIKE '%SERVERLESS%' THEN 1 ELSE 0 END) as serverless_count

      FROM system.billing.usage

      WHERE usage_date >= current_date() - INTERVAL 30 DAYS

        AND usage_type LIKE '%COMPUTE%'

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

    cluster_workers AS (

      SELECT 

        COUNT(*) as total_clusters,

        SUM(CASE WHEN worker_count > 1 THEN 1 ELSE 0 END) as clusters_multi_worker,

        SUM(CASE WHEN worker_count > 3 THEN 1 ELSE 0 END) as clusters_large

      FROM (

        SELECT worker_count, delete_time,

               ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS rn

        FROM system.compute.clusters

        WHERE change_time >= current_date() - INTERVAL 30 DAYS

      ) WHERE rn = 1 AND delete_time IS NULL

    ),

    python_udfs AS (

      SELECT COUNT(*) as python_udf_count

      FROM system.information_schema.routines

      WHERE external_language = 'Python'

    ),

    cluster_policies AS (

      SELECT
        COUNT(*) as total_clusters,
        SUM(CASE WHEN policy_id IS NOT NULL THEN 1 ELSE 0 END) as policy_clusters

      FROM (

        SELECT policy_id,

               ROW_NUMBER() OVER (PARTITION BY account_id, workspace_id, cluster_id ORDER BY change_time DESC) AS rn

        FROM system.compute.clusters

        WHERE change_time >= current_date() - INTERVAL 30 DAYS

          AND cluster_source IN ('API', 'UI')

      ) WHERE rn = 1

    ),

    waf_status AS (

      SELECT
        waf_id,
        principle,
        best_practice,
        CASE 
        WHEN waf_id = 'PE-01-01' THEN (
          SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
        )
        WHEN waf_id = 'PE-01-02' THEN (
          CASE WHEN EXISTS (SELECT 1 FROM system.billing.usage WHERE sku_name LIKE '%SERVERLESS_REAL_TIME_INFERENCE%' LIMIT 1) THEN 100 ELSE 0 END
        )
        WHEN waf_id = 'PE-02-02' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_multi_worker * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
        )
        WHEN waf_id = 'PE-02-04' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_large * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
        )
        WHEN waf_id = 'PE-02-05' THEN (
          SELECT CASE WHEN python_udf_count = 0 THEN 100 ELSE 0 END FROM python_udfs
        )
        WHEN waf_id = 'PE-02-06' THEN (
          SELECT CASE WHEN total_compute > 0 THEN (photon_compute * 100.0 / total_compute) ELSE 0 END FROM photon_usage
        )
        WHEN waf_id = 'PE-02-07' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (policy_clusters * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
        )
        ELSE 0
        END AS current_percentage,

        CASE 
        WHEN waf_id = 'PE-01-01' AND (
          SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
        ) >= 50 THEN 'Yes'
        WHEN waf_id = 'PE-01-02' AND EXISTS (
          SELECT 1 FROM system.billing.usage WHERE sku_name LIKE '%SERVERLESS_REAL_TIME_INFERENCE%' LIMIT 1
        ) THEN 'Yes'
        WHEN waf_id = 'PE-02-02' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_multi_worker * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'PE-02-04' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (clusters_large * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
        ) >= 50 THEN 'Yes'
        WHEN waf_id = 'PE-02-05' AND (
          SELECT python_udf_count FROM python_udfs
        ) = 0 THEN 'Yes'
        WHEN waf_id = 'PE-02-06' AND (
          SELECT CASE WHEN total_compute > 0 THEN (photon_compute * 100.0 / total_compute) ELSE 0 END FROM photon_usage
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'PE-02-07' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (policy_clusters * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
        ) >= 50 THEN 'Yes'
        ELSE 'No'
        END AS implemented

      FROM (
        SELECT * FROM VALUES
        ('PE-01-01', 'Utilize serverless capabilities', 'Use serverless architecture'),
        ('PE-01-02', 'Utilize serverless capabilities', 'Use an enterprise grade model serving service'),
        ('PE-02-02', 'Design workloads for performance', 'Use parallel computation where it is beneficial'),
        ('PE-02-04', 'Design workloads for performance', 'Prefer larger clusters'),
        ('PE-02-05', 'Design workloads for performance', 'Use native Spark operations'),
        ('PE-02-06', 'Design workloads for performance', 'Use native platform engines'),
        ('PE-02-07', 'Design workloads for performance', 'Understand your hardware and workload type')
        AS waf(waf_id, principle, best_practice)
      )

    )

    SELECT
      waf_id,
      principle,
      best_practice,
      ROUND(current_percentage, 1) as score_percentage,
      CASE 
      WHEN waf_id = 'PE-01-01' THEN 50
      WHEN waf_id = 'PE-01-02' THEN 100
      WHEN waf_id = 'PE-02-02' THEN 80
      WHEN waf_id = 'PE-02-04' THEN 50
      WHEN waf_id = 'PE-02-05' THEN 100
      WHEN waf_id = 'PE-02-06' THEN 80
      WHEN waf_id = 'PE-02-07' THEN 50
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

### PE-01-01 — Use serverless architecture

| Field | Value |
|---|---|
| Principle | Utilize serverless capabilities |
| Threshold | 50% |
| waf_cache table | `waf_controls_p` |

**What it measures**

% of compute usage running on serverless SKUs (from `system.billing.usage` where `sku_name` or `usage_type` contains `SERVERLESS`).

**Recommendation if Not Met**

Drive more workloads onto serverless compute for faster startup and better efficiency.

- Serverless SQL warehouses: <https://docs.databricks.com/aws/en/admin/sql/serverless>
- Serverless pipelines: <https://docs.databricks.com/aws/en/ldp/serverless>
- Start with interactive BI + scheduled queries; then expand to eligible ETL.

**Detail Query**

??? note "View SQL"
    ```sql
    WITH CTE AS (
      SELECT
        COUNT(*) AS runs,
        SUM(usage_quantity) AS dbu_usage,
        CASE WHEN billing_origin_product = 'ALL_PURPOSE' THEN 'INTERACTIVE'
             ELSE billing_origin_product END AS billing_origin_product,
        CASE WHEN sku_name LIKE '%SERVERLESS%' OR product_features.is_serverless = true
             THEN true ELSE false END AS is_serverless
      FROM system.billing.usage 
      WHERE usage_date BETWEEN current_date() - :rollback_days AND current_date()
        AND usage_unit = 'DBU'
        AND billing_origin_product IN ('JOBS','MODEL_SERVING','LAKEFLOW_CONNECT','SQL','INTERACTIVE','DLT','ALL_PURPOSE')
      GROUP BY 2, 4
    )
    SELECT 
        billing_origin_product,
        SUM(runs) AS runs_total,
        SUM(dbu_usage) AS dbu_usage_total,
        SUM(CASE WHEN is_serverless = true THEN dbu_usage ELSE 0 END) AS sum_serverless_dbu,
        SUM(CASE WHEN is_serverless = true THEN dbu_usage ELSE 0 END)/SUM(dbu_usage) AS pct_serverless_dbu
    FROM CTE
    GROUP BY billing_origin_product 
    ORDER BY runs_total DESC;
    ```

---

### PE-01-02 — Use an enterprise grade model serving service

| Field | Value |
|---|---|
| Principle | Utilize serverless capabilities |
| Threshold | 100% |
| waf_cache table | `waf_controls_p` |

**What it measures**

Enterprise-grade real-time inference usage present (checks `sku_name` contains `SERVERLESS_REAL_TIME_INFERENCE`). Score is 100 if any such usage exists, 0 otherwise.

**Recommendation if Not Met**

Adopt Mosaic AI Model Serving (including serverless real-time inference SKUs) for enterprise inference.

- Model Serving overview: <https://docs.databricks.com/aws/en/machine-learning/model-serving/>
- Use route-optimized endpoints and autoscaling to meet latency/SLA targets.
- Monitor serving costs via system tables: <https://docs.databricks.com/aws/en/admin/system-tables/model-serving-cost>

**Detail Query**

??? note "View SQL"
    ```sql
    select usage_metadata.endpoint_name endpoint_name,
      billing_origin_product,
      sum(usage_quantity) usage_dbus
    from system.billing.usage
    WHERE sku_name LIKE '%SERVERLESS_REAL_TIME_INFERENCE%'
      AND usage_date >= current_timestamp() - interval 7 days
      AND usage_metadata.endpoint_name is not null
    group by endpoint_name, billing_origin_product
    order by usage_dbus desc
    ```

---

### PE-02-02 — Use parallel computation where it is beneficial

| Field | Value |
|---|---|
| Principle | Design workloads for performance |
| Threshold | 80% |
| waf_cache table | `waf_controls_p` |

**What it measures**

% of clusters with more than 1 worker (parallel compute), from `system.compute.clusters`.

**Recommendation if Not Met**

Refactor workloads to exploit parallelism: partitioning, parallel reads/writes, and adequate worker counts.

- Use compute autoscaling where appropriate: <https://docs.databricks.com/aws/en/compute/configure>
- Avoid single-node clusters for distributed ETL unless it's intentionally small.
- Benchmark and right-size using job metrics and query history.

**Detail Query**

??? note "View SQL"
    ```sql
    -- waf_PE-02-*_cluster_metrics
    WITH usage AS (    
      SELECT usage_metadata.cluster_id AS cluster_id, account_id, workspace_id,
        count(*) as runs, SUM(usage_quantity) AS dbu_usage
      FROM system.billing.usage 
      WHERE usage_date BETWEEN current_date()-30 AND current_date()
        AND usage_metadata.cluster_id IS NOT NULL
      GROUP BY account_id, workspace_id, usage_metadata.cluster_id
    ),
    compute_met AS (
      SELECT * FROM (
        select row_number() over(partition by account_id, workspace_id, cluster_id order by change_time desc) AS rn,
          account_id, workspace_id, c.cluster_id, c.cluster_name, c.worker_node_type,
          worker_count, max_autoscale_workers, min_autoscale_workers
        from system.compute.clusters c
      )
      WHERE rn = 1
    )
    SELECT *, row_number() over(order by dbu_usage desc) AS rank
    FROM (
      SELECT SUM(u.dbu_usage) AS dbu_usage, SUM(u.runs) AS runs, c.cluster_id, c.cluster_name, c.worker_node_type,
        CASE WHEN ifnull(worker_count,ifnull(max_autoscale_workers,0)) > 1 THEN 'Multi-Node' ELSE 'Single-Node' END AS is_multi_worker,
        ifnull(worker_count,ifnull(max_autoscale_workers,0)) AS max_worker_count,
        CASE WHEN ifnull(c.min_autoscale_workers,0) = ifnull(c.max_autoscale_workers,0) THEN 0 ELSE 1 END AS is_autoscaling
      FROM usage u
      INNER JOIN compute_met c ON u.cluster_id = c.cluster_id AND u.account_id = c.account_id AND u.workspace_id = c.workspace_id
      GROUP BY c.cluster_id, c.cluster_name, c.worker_node_type,
        CASE WHEN ifnull(worker_count,ifnull(max_autoscale_workers,0)) > 1 THEN 'Multi-Node' ELSE 'Single-Node' END,
        ifnull(worker_count,ifnull(max_autoscale_workers,0)),
        CASE WHEN ifnull(c.min_autoscale_workers,0) = ifnull(c.max_autoscale_workers,0) THEN 0 ELSE 1 END
    )
    ```

---

### PE-02-04 — Prefer larger clusters

| Field | Value |
|---|---|
| Principle | Design workloads for performance |
| Threshold | 50% |
| waf_cache table | `waf_controls_p` |

**What it measures**

% of clusters considered 'large' by worker count thresholds in query (worker_count > 3).

**Recommendation if Not Met**

Right-size compute for heavy workloads (scale up/out) and avoid chronic under-provisioning.

- Compute configuration (workers, autoscaling): <https://docs.databricks.com/aws/en/compute/configure>
- Use workload-specific policy families (ETL-large, BI-large) and enforce minimums.
- Track saturation symptoms (spill, long GC, queueing) and iterate.

---

### PE-02-05 — Use native Spark operations

| Field | Value |
|---|---|
| Principle | Design workloads for performance |
| Threshold | 100% |
| waf_cache table | `waf_controls_p` |

**What it measures**

Score = 100 if no Python UDFs found in `system.information_schema.routines`; 0 if any Python UDFs exist.

!!! tip "Why Python UDFs hurt performance"
    Python UDFs introduce serialization overhead between the JVM and Python runtime, and prevent the Catalyst optimizer from pushing predicates through UDF boundaries. Native Spark SQL functions and pandas UDFs (vectorized) avoid these costs.

**Recommendation if Not Met**

Migrate Python UDFs to native Spark SQL functions or Spark DataFrame operations.

- Use Spark SQL built-in functions wherever possible: <https://spark.apache.org/docs/latest/api/sql/>
- Where UDFs are necessary, prefer pandas UDFs (vectorized) over row-based Python UDFs.
- Review existing Python UDFs with: `SELECT routine_catalog, routine_schema, routine_name FROM system.information_schema.routines WHERE external_language = 'Python'`

**Detail Query**

??? note "View SQL"
    ```sql
    -- waf_PE-02-05_python_udfs
    SELECT COUNT(*) as count, routine_catalog as catalog_name,
      routine_schema AS schema_name,
      concat(routine_catalog,'.',routine_schema) AS full_schema
    FROM system.information_schema.routines
    WHERE external_language = 'Python' 
    GROUP BY routine_catalog, routine_schema 
    ORDER BY count DESC;
    ```

---

### PE-02-06 — Use native platform engines

| Field | Value |
|---|---|
| Principle | Design workloads for performance |
| Threshold | 80% |
| waf_cache table | `waf_controls_p` |

**What it measures**

% of compute usage with Photon enabled (`product_features.is_photon = true` or `sku_name LIKE '%PHOTON%'`).

**Recommendation if Not Met**

Enable Photon broadly for eligible workloads to improve performance efficiency.

- Photon overview and enablement: <https://docs.databricks.com/aws/en/compute/photon>
- Validate with representative ETL/SQL jobs; monitor runtime/DBU changes.

**Detail Query**

??? note "View SQL"
    ```sql
    -- waf_PE-02-06_photon_workloads
    WITH CTE AS (
      SELECT
        COUNT(*) AS runs,
        SUM(usage_quantity) AS dbu_usage,
        billing_origin_product,
        CASE WHEN sku_name LIKE '%PHOTON%' OR product_features.is_photon = true
             THEN true ELSE false END AS is_photon
      FROM system.billing.usage 
      WHERE usage_date BETWEEN current_date()-30 AND current_date()
        AND billing_origin_product IN ('JOBS','LAKEFLOW_CONNECT','VECTOR_SEARCH','DATABASE','DLT','ALL_PURPOSE','ONLINE_TABLES','INTERACTIVE')
        AND usage_unit = 'DBU'
      GROUP BY billing_origin_product, 4
    )
    SELECT 
        billing_origin_product,
        SUM(runs) AS runs_total,
        SUM(dbu_usage) AS dbu_usage_total,
        SUM(CASE WHEN is_photon = true THEN dbu_usage ELSE 0 END) AS sum_photon_dbu,
        SUM(CASE WHEN is_photon = true THEN dbu_usage ELSE 0 END)/SUM(dbu_usage) AS pct_photon_dbu
    FROM CTE
    GROUP BY billing_origin_product 
    ORDER BY runs_total DESC;
    ```

---

### PE-02-07 — Understand your hardware and workload type

| Field | Value |
|---|---|
| Principle | Design workloads for performance |
| Threshold | 50% |
| waf_cache table | `waf_controls_p` |

**What it measures**

% of active interactive clusters (`cluster_source IN ('API', 'UI')`) that have a cluster policy attached (`policy_id IS NOT NULL`).

!!! note "PE-02-07 fix"
    An earlier version of this control used serverless adoption as a proxy for hardware awareness. The current query directly measures policy attachment on interactive clusters, which more accurately reflects whether teams are being guided to appropriate hardware families.

**Recommendation if Not Met**

Attach cluster policies to interactive clusters to enforce hardware selection and workload guidelines.

- Cluster policy overview: <https://docs.databricks.com/aws/en/compute/clusters-manage#cluster-policy>
- Create policies per workload type (ETL, BI, ML) with appropriate instance families and sizes.
- Policies help ensure appropriate hardware is selected for each workload type.

---
