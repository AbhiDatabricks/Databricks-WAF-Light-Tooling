#!/usr/bin/env python3
"""
Update Summary tab query to use the same percentage-based logic from all pillars
"""
import json

print("📊 Updating Summary Tab Query...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

def find_dataset(dashboard, display_name):
    """Find a dataset by display name"""
    for dataset in dashboard.get('datasets', []):
        if dataset.get('displayName') == display_name:
            return dataset
    return None

# Build comprehensive query with all CTEs and logic from all pillars
summary_query = """WITH delta_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG') THEN 1 ELSE 0 END) as delta_tables
  FROM system.information_schema.tables
  WHERE table_catalog != 'hive_metastore'
),
lineage_usage AS (
  SELECT 
    COUNT(DISTINCT t.table_full_name) as total_tables,
    COUNT(DISTINCT CASE WHEN tl.target_table_full_name IS NOT NULL THEN t.table_full_name END) as lineage_tables
  FROM system.information_schema.tables t
  LEFT JOIN system.access.table_lineage tl ON t.table_full_name = tl.target_table_full_name
  WHERE t.table_catalog != 'hive_metastore'
),
metadata_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN comment IS NOT NULL THEN 1 ELSE 0 END) as tables_with_comments,
    SUM(CASE WHEN EXISTS (
      SELECT 1 FROM system.information_schema.table_tags tt 
      WHERE tt.table_full_name = t.table_full_name
    ) THEN 1 ELSE 0 END) as tables_with_tags
  FROM system.information_schema.tables t
  WHERE table_catalog != 'hive_metastore'
),
serverless_usage AS (
  SELECT 
    COUNT(*) as total_compute,
    SUM(CASE WHEN usage_type LIKE '%SERVERLESS%' OR sku_name LIKE '%SERVERLESS%' THEN 1 ELSE 0 END) as serverless_count
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
),
photon_usage AS (
  SELECT 
    COUNT(*) as total_queries,
    SUM(CASE WHEN photon_enabled = true THEN 1 ELSE 0 END) as photon_queries
  FROM system.query.history
  WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
),
sql_warehouse_usage AS (
  SELECT 
    COUNT(*) as total_compute,
    SUM(CASE WHEN usage_type LIKE '%SQL%' THEN 1 ELSE 0 END) as sql_compute
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
),
cluster_policies AS (
  SELECT 
    COUNT(*) as total_clusters,
    SUM(CASE WHEN policy_id IS NOT NULL THEN 1 ELSE 0 END) as clusters_with_policy
  FROM system.compute.clusters
),
cluster_tags AS (
  SELECT 
    COUNT(*) as total_clusters,
    SUM(CASE WHEN size(map_keys(tags)) > 0 THEN 1 ELSE 0 END) as clusters_with_tags
  FROM system.compute.clusters
),
cluster_workers AS (
  SELECT 
    COUNT(*) as total_clusters,
    SUM(CASE WHEN worker_count > 1 THEN 1 ELSE 0 END) as clusters_multi_worker,
    SUM(CASE WHEN worker_count > 3 THEN 1 ELSE 0 END) as clusters_large
  FROM system.compute.clusters
),
instance_variety AS (
  SELECT 
    COUNT(*) as total_clusters,
    COUNT(DISTINCT split(worker_node_type,'[.]')[0]) as distinct_families
  FROM system.compute.clusters
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
waf_status AS (
  SELECT
    waf_id,
    CASE 
    -- Governance (DG)
    WHEN waf_id = 'DG-01-03' AND (
      SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage
    ) >= 50 THEN 'Yes'
    WHEN waf_id = 'DG-01-04' AND (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    ) >= 50 THEN 'Yes'
    WHEN waf_id = 'DG-01-05' AND (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_tags * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    ) >= 50 THEN 'Yes'
    WHEN waf_id = 'DG-02-01' AND EXISTS (SELECT 1 FROM system.information_schema.row_filters LIMIT 1) THEN 'Yes'
    WHEN waf_id = 'DG-02-02' AND EXISTS (SELECT 1 FROM system.access.audit LIMIT 1) THEN 'Yes'
    WHEN waf_id = 'DG-02-03' AND EXISTS (
      SELECT 1 FROM system.information_schema.tables
      WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'
      LIMIT 1
    ) THEN 'Yes'
    WHEN waf_id = 'DG-03-02' AND EXISTS (
      SELECT 1 FROM system.information_schema.tables 
      WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 
      LIMIT 1
    ) THEN 'Yes'
    WHEN waf_id = 'DG-03-03' AND (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    ) >= 80 THEN 'Yes'
    -- Cost (CO)
    WHEN waf_id = 'CO-01-01' AND (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'CO-01-03' AND (
      SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
    ) >= 50 THEN 'Yes'
    WHEN waf_id = 'CO-01-04' AND EXISTS (SELECT 1 FROM system.compute.clusters WHERE dbr_version IS NOT NULL LIMIT 1) THEN 'Yes'
    WHEN waf_id = 'CO-01-06' AND (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    ) >= 50 THEN 'Yes'
    WHEN waf_id = 'CO-01-09' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'CO-02-03' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'CO-03-01' AND EXISTS (SELECT 1 FROM system.billing.usage LIMIT 1) THEN 'Yes'
    WHEN waf_id = 'CO-03-02' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'CO-03-03' AND EXISTS (SELECT 1 FROM system.billing.usage LIMIT 1) THEN 'Yes'
    -- Performance (PE)
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
    WHEN waf_id = 'PE-02-05' AND NOT EXISTS (
      SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1
    ) THEN 'Yes'
    WHEN waf_id = 'PE-02-06' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'PE-02-07' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (distinct_families * 100.0 / total_clusters) ELSE 0 END FROM instance_variety
    ) >= 5 THEN 'Yes'
    -- Reliability (R)
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
    END AS implemented,
    CASE 
    WHEN waf_id LIKE 'DG-%' THEN 'Data & AI Governance'
    WHEN waf_id LIKE 'CO-%' THEN 'Cost Optimization'
    WHEN waf_id LIKE 'PE-%' THEN 'Performance Efficiency'
    WHEN waf_id LIKE 'R-%'  THEN 'Reliability'
    END AS pillar
  FROM (
    SELECT * FROM VALUES
    ('DG-01-03'), ('DG-01-04'), ('DG-01-05'),
    ('DG-02-01'), ('DG-02-02'), ('DG-02-03'),
    ('DG-03-02'), ('DG-03-03'),
    ('CO-01-01'), ('CO-01-03'), ('CO-01-04'), ('CO-01-06'), ('CO-01-09'),
    ('CO-02-03'), ('CO-03-01'), ('CO-03-02'), ('CO-03-03'),
    ('PE-01-01'), ('PE-01-02'),
    ('PE-02-02'), ('PE-02-04'), ('PE-02-05'), ('PE-02-06'), ('PE-02-07'),
    ('R-01-01'), ('R-01-03'), ('R-01-05'), ('R-01-06'),
    ('R-02-03'), ('R-02-04'),
    ('R-03-01'), ('R-03-02')
    AS waf(waf_id)
  )
)
SELECT
  pillar,
  COUNT(*) AS total_controls,
  SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) AS implemented_controls,
  ROUND(100 * SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 0) AS completion_percent
FROM waf_status
GROUP BY pillar
ORDER BY pillar;
"""

# Update Summary dataset
dataset = find_dataset(dashboard, 'total_percentage_across_pillars')
if dataset:
    dataset['queryLines'] = summary_query.split('\n')
    print("✅ Updated total_percentage_across_pillars")
else:
    print("❌ Dataset total_percentage_across_pillars not found")

# Save dashboard
print("\n💾 Saving dashboard...")
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Summary tab updated with percentage-based logic!")
print("="*70)
