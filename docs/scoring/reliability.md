# Reliability — Scoring Methodology

This pillar assesses how well your workspace is designed for failure tolerance, data integrity, managed services adoption, and autoscaling — the pillars of a resilient Databricks environment.

## How scores are calculated

The WAF Reload job runs the control scoring query below against Databricks system tables and stores results in `waf_cache.waf_controls_r`. Each control receives a percentage score (0–100). If the score meets or exceeds the threshold, the control is marked **Met**.

## Control Scoring Query

The following SQL computes scores for all Reliability controls. Run by the WAF Reload job and stored in `waf_cache.waf_controls_r`.

??? note "View SQL"
    ```sql
    WITH delta_usage AS (

      SELECT 

        COUNT(*) as total_tables,

        SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG', 'DELTASHARING') THEN 1 ELSE 0 END) as delta_tables

      FROM system.information_schema.tables

      WHERE table_catalog != 'hive_metastore'

        AND table_type IN ('MANAGED', 'EXTERNAL')

    ),

    dlt_usage AS (

      SELECT 

        COUNT(*) as total_compute_usage,

        SUM(CASE WHEN billing_origin_product = 'DLT' THEN 1 ELSE 0 END) as dlt_compute_usage

      FROM system.billing.usage

      WHERE usage_date >= current_date() - INTERVAL 30 DAYS

        AND usage_type LIKE '%COMPUTE%'

    ),

    model_serving_usage AS (

      SELECT 

        COUNT(*) as total_ml_compute,

        SUM(CASE WHEN billing_origin_product = 'MODEL_SERVING' THEN 1 ELSE 0 END) as serving_compute

      FROM system.billing.usage

      WHERE usage_date >= current_date() - INTERVAL 30 DAYS

        AND (usage_type LIKE '%COMPUTE%' OR billing_origin_product = 'MODEL_SERVING')

    ),

    serverless_usage AS (

      SELECT 

        COUNT(*) as total_compute,

        SUM(CASE WHEN usage_type LIKE '%SERVERLESS%' OR sku_name LIKE '%SERVERLESS%' THEN 1 ELSE 0 END) as serverless_count

      FROM system.billing.usage

      WHERE usage_date >= current_date() - INTERVAL 30 DAYS

        AND usage_type LIKE '%COMPUTE%'

    ),

    autoscale_clusters AS (

      SELECT
        COUNT(*) as total_clusters,
        SUM(CASE WHEN ifnull(max_autoscale_workers, 0) > 0 THEN 1 ELSE 0 END) as autoscale_clusters

      FROM (

        SELECT max_autoscale_workers, delete_time,

               ROW_NUMBER() OVER (PARTITION BY cluster_id ORDER BY change_time DESC) AS rn

        FROM system.compute.clusters

        WHERE change_time >= current_date() - INTERVAL 30 DAYS

      ) WHERE rn = 1 AND delete_time IS NULL

    ),

    autoscale_warehouses AS (

      SELECT
        COUNT(*) as total_warehouses,
        SUM(CASE WHEN max_clusters > min_clusters THEN 1 ELSE 0 END) as autoscale_warehouses

      FROM (

        SELECT warehouse_id, min_clusters, max_clusters, delete_time,

               ROW_NUMBER() OVER (PARTITION BY warehouse_id ORDER BY change_time DESC) AS rn

        FROM system.compute.warehouses

        WHERE change_time >= current_timestamp() - INTERVAL 30 DAYS

          AND warehouse_type IN ('CLASSIC', 'PRO')

      ) WHERE rn = 1 AND delete_time IS NULL

    ),

    waf_status AS (

      SELECT
        waf_id,
        principle,
        best_practice,
        CASE 
        -- R-01-01: >80% of tables use Delta/ICEBERG format
        WHEN waf_id = 'R-01-01' THEN (
          SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
        )
        -- R-01-03: >30% of compute usage is DLT
        WHEN waf_id = 'R-01-03' THEN (
          SELECT CASE WHEN total_compute_usage > 0 THEN (dlt_compute_usage * 100.0 / total_compute_usage) ELSE 0 END FROM dlt_usage
        )
        -- R-01-05: >20% of ML compute is Model Serving
        WHEN waf_id = 'R-01-05' THEN (
          SELECT CASE WHEN total_ml_compute > 0 THEN (serving_compute * 100.0 / total_ml_compute) ELSE 0 END FROM model_serving_usage
        )
        -- R-01-06: >50% of compute is serverless or managed
        WHEN waf_id = 'R-01-06' THEN (
          SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
        )
        -- R-02-04: >30% of compute usage is DLT (same metric as R-01-03)
        WHEN waf_id = 'R-02-04' THEN (
          SELECT CASE WHEN total_compute_usage > 0 THEN (dlt_compute_usage * 100.0 / total_compute_usage) ELSE 0 END FROM dlt_usage
        )
        -- R-03-01: >80% of clusters have auto-scaling
        WHEN waf_id = 'R-03-01' THEN (
          SELECT CASE WHEN total_clusters > 0 THEN (autoscale_clusters * 100.0 / total_clusters) ELSE 0 END FROM autoscale_clusters
        )
        -- R-03-02: >80% of warehouses have auto-scaling
        WHEN waf_id = 'R-03-02' THEN (
          SELECT CASE WHEN total_warehouses > 0 THEN (autoscale_warehouses * 100.0 / total_warehouses) ELSE 0 END FROM autoscale_warehouses
        )
        ELSE 0
        END AS current_percentage,

        CASE 
        WHEN waf_id = 'R-01-01' AND (
          SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'R-01-03' AND (
          SELECT CASE WHEN total_compute_usage > 0 THEN (dlt_compute_usage * 100.0 / total_compute_usage) ELSE 0 END FROM dlt_usage
        ) >= 30 THEN 'Yes'
        WHEN waf_id = 'R-01-05' AND (
          SELECT CASE WHEN total_ml_compute > 0 THEN (serving_compute * 100.0 / total_ml_compute) ELSE 0 END FROM model_serving_usage
        ) >= 20 THEN 'Yes'
        WHEN waf_id = 'R-01-06' AND (
          SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
        ) >= 50 THEN 'Yes'
        WHEN waf_id = 'R-02-04' AND (
          SELECT CASE WHEN total_compute_usage > 0 THEN (dlt_compute_usage * 100.0 / total_compute_usage) ELSE 0 END FROM dlt_usage
        ) >= 30 THEN 'Yes'
        WHEN waf_id = 'R-03-01' AND (
          SELECT CASE WHEN total_clusters > 0 THEN (autoscale_clusters * 100.0 / total_clusters) ELSE 0 END FROM autoscale_clusters
        ) >= 80 THEN 'Yes'
        WHEN waf_id = 'R-03-02' AND (
          SELECT CASE WHEN total_warehouses > 0 THEN (autoscale_warehouses * 100.0 / total_warehouses) ELSE 0 END FROM autoscale_warehouses
        ) >= 80 THEN 'Yes'
        ELSE 'No'
        END AS implemented

      FROM (
        SELECT * FROM VALUES
        ('R-01-01', 'Design for failure', 'Use a data format that supports ACID transactions'),
        ('R-01-03', 'Design for failure', 'Automatically rescue invalid or nonconforming data'),
        ('R-01-05', 'Design for failure', 'Use a scalable and production-grade model serving infrastructure'),
        ('R-01-06', 'Design for failure', 'Use managed services for your workloads'),
        ('R-02-04', 'Manage data quality', 'Use constraints and data expectations'),
        ('R-03-01', 'Design for autoscaling', 'Enable autoscaling for ETL workloads'),
        ('R-03-02', 'Design for autoscaling', 'Use autoscaling for SQL Warehouses')
        AS waf(waf_id, principle, best_practice)
      )

    )

    SELECT
      waf_id,
      principle,
      best_practice,
      ROUND(current_percentage, 1) as score_percentage,
      CASE 
        WHEN waf_id = 'R-01-01' THEN 80
        WHEN waf_id = 'R-01-03' THEN 30
        WHEN waf_id = 'R-01-05' THEN 20
        WHEN waf_id = 'R-01-06' THEN 50
        WHEN waf_id = 'R-02-04' THEN 30
        WHEN waf_id = 'R-03-01' THEN 80
        WHEN waf_id = 'R-03-02' THEN 80
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

### R-01-01 — Use a data format that supports ACID transactions

| Field | Value |
|---|---|
| Principle | Design for failure |
| Threshold | 80% |
| waf_cache table | `waf_controls_r` |

**What it measures**

% of UC tables stored in `DELTA` or `ICEBERG` format (ACID-capable), from `system.information_schema.tables`.

**Recommendation if Not Met**

Standardize on Delta/Iceberg tables for transactional reliability.

- Delta Lake overview: <https://docs.databricks.com/aws/en/delta/>
- ACID guarantees explanation: <https://docs.databricks.com/aws/en/lakehouse/acid>
- Prioritize critical datasets and pipelines; add schema enforcement and expectations where appropriate.

---

### R-01-03 — Automatically rescue invalid or nonconforming data

| Field | Value |
|---|---|
| Principle | Design for failure |
| Threshold | 30% |
| waf_cache table | `waf_controls_r` |

**What it measures**

% of compute usage attributed to Lakeflow/Delta Live Tables pipelines (from `system.billing.usage` where `billing_origin_product = 'DLT'`).

!!! note "Shared metric with R-02-04"
    R-01-03 and R-02-04 both use the DLT compute share as their metric. R-01-03 frames it as failure isolation (rescued data), R-02-04 as data quality (expectations). The threshold and scoring logic are identical.

**Recommendation if Not Met**

Increase adoption of managed pipelines (Lakeflow Spark Declarative Pipelines / DLT) for built-in orchestration, quality, and recovery.

- Configure serverless pipelines: <https://docs.databricks.com/aws/en/ldp/serverless>
- Lakeflow SDP overview: <https://docs.databricks.com/gcp/en/ldp/>
- Migrate brittle jobs first (multi-step ETL with retries/backfills); standardize expectations and monitoring.

---

### R-01-05 — Use a scalable and production-grade model serving infrastructure

| Field | Value |
|---|---|
| Principle | Design for failure |
| Threshold | 20% |
| waf_cache table | `waf_controls_r` |

**What it measures**

% of ML compute usage attributed to Mosaic AI Model Serving (`billing_origin_product = 'MODEL_SERVING'`).

**Recommendation if Not Met**

Use Mosaic AI Model Serving for production inference (reliability, scaling, governance).

- Model Serving overview: <https://docs.databricks.com/aws/en/machine-learning/model-serving/>
- Cost/usage monitoring via system tables: <https://docs.databricks.com/aws/en/admin/system-tables/model-serving-cost>
- Move ad-hoc notebook inference to endpoints; set autoscaling + logging/monitoring and rollout strategy.

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

### R-01-06 — Use managed services for your workloads

| Field | Value |
|---|---|
| Principle | Design for failure |
| Threshold | 50% |
| waf_cache table | `waf_controls_r` |

**What it measures**

% of compute usage running on serverless SKUs (from `system.billing.usage` where `sku_name` or `usage_type` contains `SERVERLESS`).

**Recommendation if Not Met**

Prefer serverless for steady-state reliability (fewer cluster ops) where workload/network constraints allow.

- Serverless SQL warehouses: <https://docs.databricks.com/aws/en/admin/sql/serverless>
- Serverless pipelines: <https://docs.databricks.com/aws/en/ldp/serverless>
- Define 'serverless-first' defaults in your platform standards and exceptions process.

---

### R-02-04 — Use constraints and data expectations

| Field | Value |
|---|---|
| Principle | Manage data quality |
| Threshold | 30% |
| waf_cache table | `waf_controls_r` |

**What it measures**

Same as R-01-03: DLT/Lakeflow usage share (data pipeline reliability), measured as % of compute usage attributed to `billing_origin_product = 'DLT'`.

**Recommendation if Not Met**

Increase adoption of managed pipelines (Lakeflow Spark Declarative Pipelines / DLT) for built-in orchestration, quality, and recovery.

- Configure serverless pipelines: <https://docs.databricks.com/aws/en/ldp/serverless>
- Lakeflow SDP overview: <https://docs.databricks.com/gcp/en/ldp/>
- Migrate brittle jobs first (multi-step ETL with retries/backfills); standardize expectations and monitoring.

---

### R-03-01 — Enable autoscaling for ETL workloads

| Field | Value |
|---|---|
| Principle | Design for autoscaling |
| Threshold | 80% |
| waf_cache table | `waf_controls_r` |

**What it measures**

% of clusters configured with autoscaling (`min_autoscale_workers` / `max_autoscale_workers` not null), from `system.compute.clusters`.

**Recommendation if Not Met**

Increase cluster autoscaling coverage to handle workload variability without manual intervention.

- Autoscaling configuration guidance: <https://docs.databricks.com/aws/en/compute/configure>
- Compute system tables reference (autoscale fields): <https://docs.databricks.com/aws/en/admin/system-tables/compute>
- Use compute policies to enforce min/max ranges and auto-termination.

**Detail Query**

??? note "View SQL"
    ```sql
    select workspace_id, cluster_id, cluster_name, owned_by, worker_count, create_time
    from system.compute.clusters 
    where cluster_source = 'JOB'
      and create_time >= current_timestamp() - interval 7 days
      and max_autoscale_workers is null
    ```

---

### R-03-02 — Use autoscaling for SQL Warehouses

| Field | Value |
|---|---|
| Principle | Design for autoscaling |
| Threshold | 80% |
| waf_cache table | `waf_controls_r` |

**What it measures**

% of SQL warehouses configured with autoscaling (`max_clusters > min_clusters`), from `system.compute.warehouses`. Only `CLASSIC` and `PRO` warehouse types are evaluated (serverless warehouses autoscale automatically).

**Recommendation if Not Met**

Enable autoscaling (and right-sizing) for SQL warehouses to meet concurrency while controlling costs.

- Warehouse sizing/scaling behavior: <https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-behavior>
- Warehouse types (consider serverless): <https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types>
- Set sensible min/max clusters; monitor queue times and tune per workload class.

**Detail Query**

??? note "View SQL"
    ```sql
    SELECT
        warehouse_id,
        warehouse_name,
        warehouse_type,
        warehouse_size,
        min_clusters,
        max_clusters,
        auto_stop_minutes
    FROM system.compute.warehouses
    QUALIFY
        ROW_NUMBER() OVER (PARTITION BY warehouse_id ORDER BY change_time DESC) = 1
        and delete_time is null
        and min_clusters = max_clusters;
    ```

---
