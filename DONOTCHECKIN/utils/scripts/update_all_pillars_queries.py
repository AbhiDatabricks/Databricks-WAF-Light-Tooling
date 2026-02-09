#!/usr/bin/env python3
"""
Update Governance, Cost, and Performance pillars with percentage-based logic
Following the same pattern as Reliability
"""
import json
import re

print("📊 Updating All Pillars with Percentage-Based Logic...")
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

def update_governance_queries():
    """Update Governance pillar queries"""
    print("\n🔧 Updating Governance Pillar...")
    
    # Shared CTEs for Governance
    governance_ctes = """WITH delta_usage AS (
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
"""
    
    # Total percentage query
    total_query = governance_ctes + """waf_status AS (
  SELECT
    waf_id,
    CASE 
    -- DG-01-03: >50% of tables have lineage tracked
    WHEN waf_id = 'DG-01-03' AND (
      SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage
    ) >= 50 THEN 'Yes'
    -- DG-01-04: >50% of tables have comments
    WHEN waf_id = 'DG-01-04' AND (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    ) >= 50 THEN 'Yes'
    -- DG-01-05: >50% of tables have tags
    WHEN waf_id = 'DG-01-05' AND (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_tags * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    ) >= 50 THEN 'Yes'
    -- DG-02-01: Row filters exist
    WHEN waf_id = 'DG-02-01' AND EXISTS (
      SELECT 1 FROM system.information_schema.row_filters LIMIT 1
    ) THEN 'Yes'
    -- DG-02-02: Audit logging exists
    WHEN waf_id = 'DG-02-02' AND EXISTS (
      SELECT 1 FROM system.access.audit LIMIT 1
    ) THEN 'Yes'
    -- DG-02-03: Marketplace audit events exist
    WHEN waf_id = 'DG-02-03' AND EXISTS (
      SELECT 1 FROM system.information_schema.tables
      WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'
      LIMIT 1
    ) THEN 'Yes'
    -- DG-03-02: Data quality tools exist
    WHEN waf_id = 'DG-03-02' AND EXISTS (
      SELECT 1 FROM system.information_schema.tables 
      WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 
      LIMIT 1
    ) THEN 'Yes'
    -- DG-03-03: >80% of tables use Delta/ICEBERG format
    WHEN waf_id = 'DG-03-03' AND (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    ) >= 80 THEN 'Yes'
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('DG-01-03'), ('DG-01-04'), ('DG-01-05'),
    ('DG-02-01'), ('DG-02-02'), ('DG-02-03'),
    ('DG-03-02'), ('DG-03-03')
    AS waf(waf_id)
  )
)
SELECT
  COUNT(*) AS total_controls,
  SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) AS implemented_controls,
  ROUND(100 * SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 0) AS completion_percent
FROM waf_status;
"""
    
    # Principal percentage query
    principal_query = governance_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
    CASE 
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
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('DG-01-03', 'Unify data and AI management'),
    ('DG-01-04', 'Unify data and AI management'),
    ('DG-01-05', 'Unify data and AI management'),
    ('DG-02-01', 'Unify data and AI security'),
    ('DG-02-02', 'Unify data and AI security'),
    ('DG-02-03', 'Unify data and AI security'),
    ('DG-03-02', 'Establish data quality standards'),
    ('DG-03-03', 'Establish data quality standards')
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
    
    # Controls query with percentages
    controls_query = governance_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
    description,
    CASE 
    WHEN waf_id = 'DG-01-03' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage
    )
    WHEN waf_id = 'DG-01-04' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    )
    WHEN waf_id = 'DG-01-05' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_tags * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    )
    WHEN waf_id = 'DG-02-01' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.row_filters LIMIT 1) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'DG-02-02' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.access.audit LIMIT 1) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'DG-02-03' THEN (
      CASE WHEN EXISTS (
        SELECT 1 FROM system.information_schema.tables
        WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'
        LIMIT 1
      ) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'DG-03-02' THEN (
      CASE WHEN EXISTS (
        SELECT 1 FROM system.information_schema.tables 
        WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 
        LIMIT 1
      ) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'DG-03-03' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    )
    ELSE 0
    END AS current_percentage,
    CASE 
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
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('DG-01-03', 'Unify data and AI management', 'Track data and AI lineage'),
    ('DG-01-04', 'Unify data and AI management', 'Add comments to metadata'),
    ('DG-01-05', 'Unify data and AI management', 'Enable easy data discovery'),
    ('DG-02-01', 'Unify data and AI security', 'Centralize access control (row/column level)'),
    ('DG-02-02', 'Unify data and AI security', 'Configure audit logging'),
    ('DG-02-03', 'Unify data and AI security', 'Audit data platform events'),
    ('DG-03-02', 'Establish data quality standards', 'Use data quality tools and profiling'),
    ('DG-03-03', 'Establish data quality standards', 'Enforce standardized data formats')
    AS waf(waf_id, principle, description)
  )
)
SELECT
  waf_id,
  principle,
  description,
  ROUND(current_percentage, 1) as score_percentage,
  CASE 
  WHEN waf_id = 'DG-01-03' THEN 50
  WHEN waf_id = 'DG-01-04' THEN 50
  WHEN waf_id = 'DG-01-05' THEN 50
  WHEN waf_id = 'DG-02-01' THEN 100
  WHEN waf_id = 'DG-02-02' THEN 100
  WHEN waf_id = 'DG-02-03' THEN 100
  WHEN waf_id = 'DG-03-02' THEN 100
  WHEN waf_id = 'DG-03-03' THEN 80
  END as threshold_percentage,
  CASE 
  WHEN implemented = 'Yes' THEN 'Met'
  ELSE 'Not Met'
  END as threshold_met,
  implemented
FROM waf_status
ORDER BY principle, waf_id;
"""
    
    # Update datasets
    for display_name, query in [
        ('total_percentage_g', total_query),
        ('waf_principal_percentage_g', principal_query),
        ('waf_controls_g', controls_query)
    ]:
        dataset = find_dataset(dashboard, display_name)
        if dataset:
            dataset['queryLines'] = query.split('\n')
            print(f"  ✅ Updated {display_name}")
        else:
            print(f"  ❌ Dataset {display_name} not found")

def update_cost_queries():
    """Update Cost pillar queries"""
    print("\n🔧 Updating Cost Optimization Pillar...")
    
    # Shared CTEs for Cost
    cost_ctes = """WITH delta_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG') THEN 1 ELSE 0 END) as delta_tables
  FROM system.information_schema.tables
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
"""
    
    # Total percentage query
    total_query = cost_ctes + """waf_status AS (
  SELECT
    waf_id,
    CASE 
    -- CO-01-01: >80% of tables use Delta/ICEBERG format
    WHEN waf_id = 'CO-01-01' AND (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    ) >= 80 THEN 'Yes'
    -- CO-01-03: >50% of compute is SQL warehouse
    WHEN waf_id = 'CO-01-03' AND (
      SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
    ) >= 50 THEN 'Yes'
    -- CO-01-04: All clusters have DBR version
    WHEN waf_id = 'CO-01-04' AND EXISTS (
      SELECT 1 FROM system.compute.clusters WHERE dbr_version IS NOT NULL LIMIT 1
    ) THEN 'Yes'
    -- CO-01-06: >50% of compute is serverless
    WHEN waf_id = 'CO-01-06' AND (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    ) >= 50 THEN 'Yes'
    -- CO-01-09: >80% of queries use Photon
    WHEN waf_id = 'CO-01-09' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'
    -- CO-02-03: >80% of clusters have compute policies
    WHEN waf_id = 'CO-02-03' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
    ) >= 80 THEN 'Yes'
    -- CO-03-01: Cost monitoring exists
    WHEN waf_id = 'CO-03-01' AND EXISTS (
      SELECT 1 FROM system.billing.usage LIMIT 1
    ) THEN 'Yes'
    -- CO-03-02: >80% of clusters have tags
    WHEN waf_id = 'CO-03-02' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
    ) >= 80 THEN 'Yes'
    -- CO-03-03: Observability exists
    WHEN waf_id = 'CO-03-03' AND EXISTS (
      SELECT 1 FROM system.billing.usage LIMIT 1
    ) THEN 'Yes'
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('CO-01-01'), ('CO-01-03'), ('CO-01-04'), ('CO-01-06'), ('CO-01-09'),
    ('CO-02-03'), ('CO-03-01'), ('CO-03-02'), ('CO-03-03')
    AS waf(waf_id)
  )
)
SELECT
  COUNT(*) AS total_controls,
  SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) AS implemented_controls,
  ROUND(100 * SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 0) AS completion_percent
FROM waf_status;
"""
    
    # Principal percentage query
    principal_query = cost_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
    CASE 
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
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('CO-01-01', 'Choose optimal resources'),
    ('CO-01-03', 'Choose optimal resources'),
    ('CO-01-04', 'Choose optimal resources'),
    ('CO-01-06', 'Choose optimal resources'),
    ('CO-01-09', 'Choose optimal resources'),
    ('CO-02-03', 'Dynamically allocate resources'),
    ('CO-03-01', 'Monitor and control cost'),
    ('CO-03-02', 'Monitor and control cost'),
    ('CO-03-03', 'Monitor and control cost')
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
    
    # Controls query with percentages
    controls_query = cost_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
    best_practice,
    CASE 
    WHEN waf_id = 'CO-01-01' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    )
    WHEN waf_id = 'CO-01-03' THEN (
      SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
    )
    WHEN waf_id = 'CO-01-04' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.compute.clusters WHERE dbr_version IS NOT NULL LIMIT 1) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'CO-01-06' THEN (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    )
    WHEN waf_id = 'CO-01-09' THEN (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    )
    WHEN waf_id = 'CO-02-03' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
    )
    WHEN waf_id = 'CO-03-01' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.billing.usage LIMIT 1) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'CO-03-02' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
    )
    WHEN waf_id = 'CO-03-03' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.billing.usage LIMIT 1) THEN 100 ELSE 0 END
    )
    ELSE 0
    END AS current_percentage,
    CASE 
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
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('CO-01-01', 'Choose optimal resources', 'Use performance optimized data formats'),
    ('CO-01-03', 'Choose optimal resources', 'Use SQL warehouse for SQL workloads'),
    ('CO-01-04', 'Choose optimal resources', 'Use up-to-date runtimes'),
    ('CO-01-06', 'Choose optimal resources', 'Use Serverless for your workloads'),
    ('CO-01-09', 'Choose optimal resources', 'Evaluate performance optimized query engines'),
    ('CO-02-03', 'Dynamically allocate resources', 'Use compute policies to control costs'),
    ('CO-03-01', 'Monitor and control cost', 'Monitor costs'),
    ('CO-03-02', 'Monitor and control cost', 'Tag clusters for cost attribution'),
    ('CO-03-03', 'Monitor and control cost', 'Implement observability to track & chargeback cost')
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
  WHEN waf_id = 'CO-01-04' THEN 100
  WHEN waf_id = 'CO-01-06' THEN 50
  WHEN waf_id = 'CO-01-09' THEN 80
  WHEN waf_id = 'CO-02-03' THEN 80
  WHEN waf_id = 'CO-03-01' THEN 100
  WHEN waf_id = 'CO-03-02' THEN 80
  WHEN waf_id = 'CO-03-03' THEN 100
  END as threshold_percentage,
  CASE 
  WHEN implemented = 'Yes' THEN 'Met'
  ELSE 'Not Met'
  END as threshold_met,
  implemented
FROM waf_status
ORDER BY principle, waf_id;
"""
    
    # Update datasets
    for display_name, query in [
        ('total_percentage_c', total_query),
        ('waf_principal_percentage_c', principal_query),
        ('waf_controls_c', controls_query)
    ]:
        dataset = find_dataset(dashboard, display_name)
        if dataset:
            dataset['queryLines'] = query.split('\n')
            print(f"  ✅ Updated {display_name}")
        else:
            print(f"  ❌ Dataset {display_name} not found")

def update_performance_queries():
    """Update Performance pillar queries"""
    print("\n🔧 Updating Performance Efficiency Pillar...")
    
    # Shared CTEs for Performance
    performance_ctes = """WITH serverless_usage AS (
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
"""
    
    # Total percentage query
    total_query = performance_ctes + """waf_status AS (
  SELECT
    waf_id,
    CASE 
    -- PE-01-01: >50% of compute is serverless
    WHEN waf_id = 'PE-01-01' AND (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    ) >= 50 THEN 'Yes'
    -- PE-01-02: Model serving exists
    WHEN waf_id = 'PE-01-02' AND EXISTS (
      SELECT 1 FROM system.billing.usage WHERE sku_name LIKE '%SERVERLESS_REAL_TIME_INFERENCE%' LIMIT 1
    ) THEN 'Yes'
    -- PE-02-02: >80% of clusters have multiple workers
    WHEN waf_id = 'PE-02-02' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_multi_worker * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
    ) >= 80 THEN 'Yes'
    -- PE-02-04: >50% of clusters are large (>3 workers)
    WHEN waf_id = 'PE-02-04' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_large * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
    ) >= 50 THEN 'Yes'
    -- PE-02-05: No Python UDFs
    WHEN waf_id = 'PE-02-05' AND NOT EXISTS (
      SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1
    ) THEN 'Yes'
    -- PE-02-06: >80% of queries use Photon
    WHEN waf_id = 'PE-02-06' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'
    -- PE-02-07: >5% instance variety
    WHEN waf_id = 'PE-02-07' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (distinct_families * 100.0 / total_clusters) ELSE 0 END FROM instance_variety
    ) >= 5 THEN 'Yes'
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('PE-01-01'), ('PE-01-02'),
    ('PE-02-02'), ('PE-02-04'), ('PE-02-05'), ('PE-02-06'), ('PE-02-07')
    AS waf(waf_id)
  )
)
SELECT
  COUNT(*) AS total_controls,
  SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) AS implemented_controls,
  ROUND(100 * SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 0) AS completion_percent
FROM waf_status;
"""
    
    # Principal percentage query
    principal_query = performance_ctes + """waf_status AS (
  SELECT
    waf_id,
    principle,
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
    WHEN waf_id = 'PE-02-05' AND NOT EXISTS (
      SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1
    ) THEN 'Yes'
    WHEN waf_id = 'PE-02-06' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'PE-02-07' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (distinct_families * 100.0 / total_clusters) ELSE 0 END FROM instance_variety
    ) >= 5 THEN 'Yes'
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
    ('PE-01-01', 'Utilize serverless capabilities'),
    ('PE-01-02', 'Utilize serverless capabilities'),
    ('PE-02-02', 'Design workloads for performance'),
    ('PE-02-04', 'Design workloads for performance'),
    ('PE-02-05', 'Design workloads for performance'),
    ('PE-02-06', 'Design workloads for performance'),
    ('PE-02-07', 'Design workloads for performance')
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
    
    # Controls query with percentages
    controls_query = performance_ctes + """waf_status AS (
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
      CASE WHEN NOT EXISTS (SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1) THEN 100 ELSE 0 END
    )
    WHEN waf_id = 'PE-02-06' THEN (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    )
    WHEN waf_id = 'PE-02-07' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (distinct_families * 100.0 / total_clusters) ELSE 0 END FROM instance_variety
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
    WHEN waf_id = 'PE-02-05' AND NOT EXISTS (
      SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1
    ) THEN 'Yes'
    WHEN waf_id = 'PE-02-06' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'
    WHEN waf_id = 'PE-02-07' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (distinct_families * 100.0 / total_clusters) ELSE 0 END FROM instance_variety
    ) >= 5 THEN 'Yes'
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
  WHEN waf_id = 'PE-02-07' THEN 5
  END as threshold_percentage,
  CASE 
  WHEN implemented = 'Yes' THEN 'Met'
  ELSE 'Not Met'
  END as threshold_met,
  implemented
FROM waf_status
ORDER BY principle, waf_id;
"""
    
    # Update datasets
    for display_name, query in [
        ('total_percentage_p', total_query),
        ('waf_principal_percentage_p', principal_query),
        ('waf_controls_p', controls_query)
    ]:
        dataset = find_dataset(dashboard, display_name)
        if dataset:
            dataset['queryLines'] = query.split('\n')
            print(f"  ✅ Updated {display_name}")
        else:
            print(f"  ❌ Dataset {display_name} not found")

# Update all pillars
update_governance_queries()
update_cost_queries()
update_performance_queries()

# Save dashboard
print("\n💾 Saving dashboard...")
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ All pillars updated with percentage-based logic!")
print("="*70)
