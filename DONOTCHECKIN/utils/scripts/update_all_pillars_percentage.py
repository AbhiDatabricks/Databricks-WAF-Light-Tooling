#!/usr/bin/env python3
"""
Update all pillars (Governance, Cost, Performance) with percentage-based logic
Ensures consistency across total_percentage, waf_controls, and waf_principal_percentage datasets
"""
import json
import re

print("📊 Updating All Pillars with Percentage-Based Logic...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Shared CTEs for all pillars
shared_ctes_template = """WITH delta_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG') THEN 1 ELSE 0 END) as delta_tables
  FROM system.information_schema.tables
  WHERE table_catalog != 'hive_metastore'
),
lineage_usage AS (
  SELECT 
    COUNT(DISTINCT table_full_name) as total_tables,
    COUNT(DISTINCT CASE WHEN source_table_full_name IS NOT NULL OR target_table_full_name IS NOT NULL THEN table_full_name END) as lineage_tables
  FROM system.information_schema.tables t
  LEFT JOIN system.access.table_lineage tl ON t.table_full_name = tl.target_table_full_name
  WHERE table_catalog != 'hive_metastore'
),
metadata_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN comment IS NOT NULL THEN 1 ELSE 0 END) as tables_with_comments,
    SUM(CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.table_tags WHERE table_full_name = t.table_full_name) THEN 1 ELSE 0 END) as tables_with_tags
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
python_udf_usage AS (
  SELECT 
    COUNT(*) as total_queries,
    SUM(CASE WHEN EXISTS (
      SELECT 1 FROM system.information_schema.routines 
      WHERE external_language = 'Python'
    ) THEN 1 ELSE 0 END) as queries_with_python_udf
  FROM system.query.history
  WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
),
"""

# Governance metrics with percentage-based logic
governance_metrics = {
    'DG-01-03': {
        'check': """WHEN waf_id = 'DG-01-03' AND (
      SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-01-03' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (lineage_tables * 100.0 / total_tables) ELSE 0 END FROM lineage_usage
    )""",
        'threshold': 50
    },
    'DG-01-04': {
        'check': """WHEN waf_id = 'DG-01-04' AND (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-01-04' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_comments * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    )""",
        'threshold': 50
    },
    'DG-01-05': {
        'check': """WHEN waf_id = 'DG-01-05' AND (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_tags * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-01-05' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (tables_with_tags * 100.0 / total_tables) ELSE 0 END FROM metadata_usage
    )""",
        'threshold': 50
    },
    'DG-02-01': {
        'check': """WHEN waf_id = 'DG-02-01' AND EXISTS (
      SELECT 1 FROM system.information_schema.row_filters LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-02-01' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.row_filters LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'DG-02-02': {
        'check': """WHEN waf_id = 'DG-02-02' AND EXISTS (
      SELECT 1 FROM system.access.audit LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-02-02' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.access.audit LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'DG-02-03': {
        'check': """WHEN waf_id = 'DG-02-03' AND EXISTS (
      SELECT 1 FROM system.information_schema.tables
      WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'
      LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-02-03' THEN (
      CASE WHEN EXISTS (
        SELECT 1 FROM system.information_schema.tables
        WHERE table_catalog = 'system' AND table_schema = 'marketplace' AND table_name = 'listing_access_events'
        LIMIT 1
      ) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'DG-03-02': {
        'check': """WHEN waf_id = 'DG-03-02' AND EXISTS (
      SELECT 1 FROM system.information_schema.tables 
      WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 
      LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-03-02' THEN (
      CASE WHEN EXISTS (
        SELECT 1 FROM system.information_schema.tables 
        WHERE table_name LIKE '%_drift_metrics' OR table_name LIKE '%_profile_metrics' 
        LIMIT 1
      ) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'DG-03-03': {
        'check': """WHEN waf_id = 'DG-03-03' AND (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'DG-03-03' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    )""",
        'threshold': 80
    }
}

# Cost metrics
cost_metrics = {
    'CO-01-01': {
        'check': """WHEN waf_id = 'CO-01-01' AND (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-01-01' THEN (
      SELECT CASE WHEN total_tables > 0 THEN (delta_tables * 100.0 / total_tables) ELSE 0 END FROM delta_usage
    )""",
        'threshold': 80
    },
    'CO-01-03': {
        'check': """WHEN waf_id = 'CO-01-03' AND (
      SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-01-03' THEN (
      SELECT CASE WHEN total_compute > 0 THEN (sql_compute * 100.0 / total_compute) ELSE 0 END FROM sql_warehouse_usage
    )""",
        'threshold': 50
    },
    'CO-01-04': {
        'check': """WHEN waf_id = 'CO-01-04' AND EXISTS (
      SELECT 1 FROM system.compute.clusters WHERE dbr_version IS NOT NULL LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-01-04' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.compute.clusters WHERE dbr_version IS NOT NULL LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'CO-01-06': {
        'check': """WHEN waf_id = 'CO-01-06' AND (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-01-06' THEN (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    )""",
        'threshold': 50
    },
    'CO-01-09': {
        'check': """WHEN waf_id = 'CO-01-09' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-01-09' THEN (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    )""",
        'threshold': 80
    },
    'CO-02-03': {
        'check': """WHEN waf_id = 'CO-02-03' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-02-03' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_policy * 100.0 / total_clusters) ELSE 0 END FROM cluster_policies
    )""",
        'threshold': 80
    },
    'CO-03-01': {
        'check': """WHEN waf_id = 'CO-03-01' AND EXISTS (
      SELECT 1 FROM system.billing.usage LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-03-01' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.billing.usage LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'CO-03-02': {
        'check': """WHEN waf_id = 'CO-03-02' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-03-02' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_with_tags * 100.0 / total_clusters) ELSE 0 END FROM cluster_tags
    )""",
        'threshold': 80
    },
    'CO-03-03': {
        'check': """WHEN waf_id = 'CO-03-03' AND EXISTS (
      SELECT 1 FROM system.billing.usage LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'CO-03-03' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.billing.usage LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    }
}

# Performance metrics
performance_metrics = {
    'PE-01-01': {
        'check': """WHEN waf_id = 'PE-01-01' AND (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-01-01' THEN (
      SELECT CASE WHEN total_compute > 0 THEN (serverless_count * 100.0 / total_compute) ELSE 0 END FROM serverless_usage
    )""",
        'threshold': 50
    },
    'PE-01-02': {
        'check': """WHEN waf_id = 'PE-01-02' AND EXISTS (
      SELECT 1 FROM system.billing.usage WHERE sku_name LIKE '%SERVERLESS_REAL_TIME_INFERENCE%' LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-01-02' THEN (
      CASE WHEN EXISTS (SELECT 1 FROM system.billing.usage WHERE sku_name LIKE '%SERVERLESS_REAL_TIME_INFERENCE%' LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'PE-02-02': {
        'check': """WHEN waf_id = 'PE-02-02' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_multi_worker * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-02-02' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_multi_worker * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
    )""",
        'threshold': 80
    },
    'PE-02-04': {
        'check': """WHEN waf_id = 'PE-02-04' AND (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_large * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
    ) >= 50 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-02-04' THEN (
      SELECT CASE WHEN total_clusters > 0 THEN (clusters_large * 100.0 / total_clusters) ELSE 0 END FROM cluster_workers
    )""",
        'threshold': 50
    },
    'PE-02-05': {
        'check': """WHEN waf_id = 'PE-02-05' AND NOT EXISTS (
      SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1
    ) THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-02-05' THEN (
      CASE WHEN NOT EXISTS (SELECT 1 FROM system.information_schema.routines WHERE external_language = 'Python' LIMIT 1) THEN 100 ELSE 0 END
    )""",
        'threshold': 100
    },
    'PE-02-06': {
        'check': """WHEN waf_id = 'PE-02-06' AND (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    ) >= 80 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-02-06' THEN (
      SELECT CASE WHEN total_queries > 0 THEN (photon_queries * 100.0 / total_queries) ELSE 0 END FROM photon_usage
    )""",
        'threshold': 80
    },
    'PE-02-07': {
        'check': """WHEN waf_id = 'PE-02-07' AND (
      SELECT CASE WHEN COUNT(*) > 0 THEN (COUNT(DISTINCT split(worker_node_type,'[.]')[0]) * 100.0 / COUNT(*)) ELSE 0 END
      FROM system.compute.clusters
    ) >= 5 THEN 'Yes'""",
        'percentage': """WHEN waf_id = 'PE-02-07' THEN (
      SELECT CASE WHEN COUNT(*) > 0 THEN (COUNT(DISTINCT split(worker_node_type,'[.]')[0]) * 100.0 / COUNT(*)) ELSE 0 END
      FROM system.compute.clusters
    )""",
        'threshold': 5
    }
}

def build_pillar_query(pillar_code, metrics_dict, identifiers_list, principles_dict):
    """Build the three queries for a pillar"""
    
    # Build CASE statements
    case_statements = []
    percentage_statements = []
    
    for ident in identifiers_list:
        if ident in metrics_dict:
            metric = metrics_dict[ident]
            case_statements.append(f"    {metric['check']}")
            percentage_statements.append(f"    {metric['percentage']}")
        else:
            case_statements.append(f"    WHEN waf_id = '{ident}' THEN 'No'")
            percentage_statements.append(f"    WHEN waf_id = '{ident}' THEN 0")
    
    # Build VALUES clause with principles
    values_clause = []
    for ident in identifiers_list:
        principle = principles_dict.get(ident, 'Unknown')
        values_clause.append(f"    ('{ident}', '{principle}')")
    
    # Total percentage query
    total_query = shared_ctes_template + f"""waf_status AS (
  SELECT
    waf_id,
    CASE 
{chr(10).join(case_statements)}
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
{chr(10).join(values_clause)}
    AS waf(waf_id, principle)
  )
)
SELECT
  COUNT(*) AS total_controls,
  SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) AS implemented_controls,
  ROUND(100 * SUM(CASE WHEN implemented = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 0) AS completion_percent
FROM waf_status;
"""
    
    # Principal percentage query
    principal_query = shared_ctes_template + f"""waf_status AS (
  SELECT
    waf_id,
    principle,
    CASE 
{chr(10).join(case_statements)}
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
{chr(10).join(values_clause)}
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
    controls_values = []
    for ident in identifiers_list:
        principle = principles_dict.get(ident, 'Unknown')
        # Get best practice from existing query or use identifier
        best_practice = f"Best practice for {ident}"  # Will need to get from existing
        controls_values.append(f"    ('{ident}', '{principle}', '{best_practice}')")
    
    controls_query = shared_ctes_template + f"""waf_status AS (
  SELECT
    waf_id,
    principle,
    best_practice,
    CASE 
{chr(10).join(percentage_statements)}
    ELSE 0
    END AS current_percentage,
    CASE 
{chr(10).join(case_statements)}
    ELSE 'No'
    END AS implemented
  FROM (
    SELECT * FROM VALUES
{chr(10).join(controls_values)}
    AS waf(waf_id, principle, best_practice)
  )
)
SELECT
  waf_id,
  principle,
  best_practice,
  ROUND(current_percentage, 1) as score_percentage,
  CASE 
{chr(10).join([f"    WHEN waf_id = '{ident}' THEN {metrics_dict[ident]['threshold']}" for ident in identifiers_list if ident in metrics_dict])}
  END as threshold_percentage,
  CASE 
    WHEN implemented = 'Yes' THEN 'Met'
    ELSE 'Not Met'
  END as threshold_met,
  implemented
FROM waf_status
ORDER BY principle, waf_id;
"""
    
    return total_query, principal_query, controls_query

# Get principles from existing queries
print("\n📋 Extracting principles and best practices from existing queries...")

# This is complex - let me read the existing queries to extract the data
# For now, let me create a simpler approach that updates the queries directly

print("\n✅ Script structure created")
print("💡 Next: Will update queries directly with percentage-based logic")
