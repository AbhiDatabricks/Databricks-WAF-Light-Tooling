#!/usr/bin/env python3
"""
Update Reliability datasets:
1. waf_controls_r - Show all 8 metrics with individual scores
2. waf_principal_percentage_r - Group by principles and calculate per-principle scores
"""
import json

print("📊 Updating Reliability Datasets...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# The shared CTEs for all Reliability queries
shared_ctes = """WITH delta_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG') THEN 1 ELSE 0 END) as delta_tables
  FROM system.information_schema.tables
  WHERE table_catalog != 'hive_metastore'
),
dlt_usage AS (
  SELECT 
    COUNT(*) as total_compute_usage,
    SUM(CASE WHEN billing_origin_product = 'DLT' THEN 1 ELSE 0 END) as dlt_compute_usage
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
),
model_serving_usage AS (
  SELECT 
    COUNT(*) as total_ml_compute,
    SUM(CASE WHEN billing_origin_product = 'MODEL_SERVING' THEN 1 ELSE 0 END) as serving_compute
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND (usage_type LIKE '%COMPUTE%' OR billing_origin_product = 'MODEL_SERVING')
),
serverless_usage AS (
  SELECT 
    COUNT(*) as total_compute,
    SUM(CASE WHEN usage_type LIKE '%SERVERLESS%' OR sku_name LIKE '%SERVERLESS%' THEN 1 ELSE 0 END) as serverless_count
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
),
autoscale_clusters AS (
  SELECT 
    COUNT(*) as total_clusters,
    SUM(CASE WHEN ifnull(max_autoscale_Workers, 0) > 0 THEN 1 ELSE 0 END) as autoscale_clusters
  FROM system.compute.clusters
),
autoscale_warehouses AS (
  SELECT 
    COUNT(*) as total_warehouses,
    SUM(CASE WHEN max_clusters - min_clusters > 0 THEN 1 ELSE 0 END) as autoscale_warehouses
  FROM system.compute.warehouses
),
"""

# Update waf_controls_r - Show all 8 metrics with scores
waf_controls_r_query = shared_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
    best_practice,
    CASE 
    -- R-01-01: >80% of tables use Delta/ICEBERG format
    WHEN waf_id = 'R-01-01' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END
      FROM delta_usage
    )
    -- R-01-03: >30% of compute usage is DLT
    WHEN waf_id = 'R-01-03' THEN (
      SELECT CASE WHEN total_compute_usage > 0 THEN (dlt_compute_usage * 100.0 / total_compute_usage) ELSE 0 END
      FROM dlt_usage
    )
    -- R-01-05: >20% of ML compute is Model Serving
    WHEN waf_id = 'R-01-05' THEN (
      SELECT CASE WHEN total_ml_compute > 0 THEN (serving_compute * 100.0 / total_ml_compute) ELSE 0 END
      FROM model_serving_usage
    )
    -- R-01-06: >50% of compute is serverless or managed
    WHEN waf_id = 'R-01-06' THEN (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END
      FROM serverless_usage
    )
    -- R-02-03: Unity Catalog metastore exists (100 if exists, 0 if not)
    WHEN waf_id = 'R-02-03' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.metastores LIMIT 1) THEN 100 ELSE 0 END
    )
    -- R-02-04: >30% of compute usage is DLT
    WHEN waf_id = 'R-02-04' THEN (
      SELECT CASE WHEN total_compute_usage > 0 THEN (dlt_compute_usage * 100.0 / total_compute_usage) ELSE 0 END
      FROM dlt_usage
    )
    -- R-03-01: >80% of clusters have auto-scaling
    WHEN waf_id = 'R-03-01' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (autoscale_clusters * 100.0 / total_clusters) ELSE 0 END
      FROM autoscale_clusters
    )
    -- R-03-02: >80% of warehouses have auto-scaling
    WHEN waf_id = 'R-03-02' THEN (
      SELECT CASE WHEN total_warehouses > 0 THEN (autoscale_warehouses * 100.0 / total_warehouses) ELSE 0 END
      FROM autoscale_warehouses
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
    WHEN waf_id = 'R-02-03' AND EXISTS (SELECT 1 FROM system.information_schema.metastores LIMIT 1) THEN 'Yes'
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
    ('R-02-03', 'Manage data quality', 'Actively manage schemas'),
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
  implemented,
  CASE 
    WHEN waf_id = 'R-01-01' THEN 80
    WHEN waf_id = 'R-01-03' THEN 30
    WHEN waf_id = 'R-01-05' THEN 20
    WHEN waf_id = 'R-01-06' THEN 50
    WHEN waf_id = 'R-02-03' THEN 100
    WHEN waf_id = 'R-02-04' THEN 30
    WHEN waf_id = 'R-03-01' THEN 80
    WHEN waf_id = 'R-03-02' THEN 80
  END as threshold_percentage
FROM waf_status
ORDER BY principle, waf_id;
"""

# Update waf_principal_percentage_r - Group by principles
waf_principal_percentage_r_query = shared_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
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
    WHEN waf_id = 'R-02-03' AND EXISTS (SELECT 1 FROM system.information_schema.metastores LIMIT 1) THEN 'Yes'
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
    ('R-01-01', 'Design for failure'),
    ('R-01-03', 'Design for failure'),
    ('R-01-05', 'Design for failure'),
    ('R-01-06', 'Design for failure'),
    ('R-02-03', 'Manage data quality'),
    ('R-02-04', 'Manage data quality'),
    ('R-03-01', 'Design for autoscaling'),
    ('R-03-02', 'Design for autoscaling')
    AS waf(waf_id, principle)
  )
)
SELECT
  principle,
  COUNT(*) AS total_controls,
  SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) AS implemented_controls,
  ROUND(100 * SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 0) AS completion_percent
FROM waf_status
GROUP BY principle
ORDER BY principle;
"""

# Update datasets
updated = 0
for dataset in dashboard.get('datasets', []):
    if dataset.get('displayName') == 'waf_controls_r':
        dataset['queryLines'] = waf_controls_r_query.split('\n')
        dataset['queryLines'] = [line + '\n' for line in dataset['queryLines'] if line.strip()]
        updated += 1
        print("✅ Updated: waf_controls_r (shows all 8 metrics with scores)")
    
    elif dataset.get('displayName') == 'waf_principal_percentage_r':
        dataset['queryLines'] = waf_principal_percentage_r_query.split('\n')
        dataset['queryLines'] = [line + '\n' for line in dataset['queryLines'] if line.strip()]
        updated += 1
        print("✅ Updated: waf_principal_percentage_r (grouped by 3 principles)")

# Save
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n{'='*70}")
print(f"✅ Updated {updated} datasets")
print("💡 Ready to deploy!")
