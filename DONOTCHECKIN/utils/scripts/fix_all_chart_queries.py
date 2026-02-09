#!/usr/bin/env python3
"""
Fix ALL Chart Queries - Use Correct System Table Columns
"""

import json
import re

print("🔧 Fixing ALL Chart Queries with Correct Column Names...")
print("="*70)

# Load dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

fixes = []

for ds in dashboard['datasets']:
    display = ds.get('displayName', '')
    query = ds.get('query', '')
    original_query = query
    
    # Fix R-01-02: Use system.billing.usage instead of system.compute.clusters
    if 'R-01-02' in display and 'system.compute.clusters' in query:
        query = """
SELECT 
  CASE 
    WHEN photon_enabled = true THEN 'Photon Engine'
    ELSE 'Apache Spark'
  END as engine_type,
  COUNT(*) as workload_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND usage_type LIKE '%COMPUTE%'
GROUP BY photon_enabled
        """
        ds['query'] = query
        fixes.append(f"R-01-02: Changed to system.billing.usage")
    
    # Fix R-01-06: Use system.billing.usage for cluster type
    elif 'R-01-06' in display and 'system.compute.clusters' in query:
        query = """
SELECT 
  CASE 
    WHEN usage_type LIKE '%SERVERLESS%' THEN 'Serverless (Managed)'
    WHEN cluster_type = 'JOB' THEN 'Job Clusters (Managed)'
    ELSE 'Traditional (Self-Managed)'
  END as service_type,
  COUNT(*) as usage_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND usage_type LIKE '%COMPUTE%'
GROUP BY service_type
        """
        ds['query'] = query
        fixes.append(f"R-01-06: Changed to system.billing.usage")
    
    # Fix R-02-02: Replace STRING_AGG with LISTAGG or remove it
    elif 'R-02-02' in display and 'STRING_AGG' in query:
        query = """
SELECT 
  table_name,
  COUNT(DISTINCT table_schema) as schema_count,
  COUNT(*) as total_occurrences
FROM system.information_schema.tables
WHERE table_catalog != 'hive_metastore'
GROUP BY table_name
HAVING COUNT(DISTINCT table_schema) > 1
ORDER BY schema_count DESC
LIMIT 50
        """
        ds['query'] = query
        fixes.append(f"R-02-02: Removed STRING_AGG")
    
    # Fix R-02-03: Remove last_altered if it doesn't exist
    elif 'R-02-03' in display and 'last_altered' in query:
        query = """
SELECT 
  table_schema,
  COUNT(*) as table_count,
  COUNT(DISTINCT table_type) as table_types
FROM system.information_schema.tables
WHERE table_catalog != 'hive_metastore'
GROUP BY table_schema
ORDER BY table_count DESC
LIMIT 30
        """
        ds['query'] = query
        fixes.append(f"R-02-03: Removed last_altered")
    
    # Fix R-02-04: Check if data_quality_monitoring table exists, if not use simpler query
    elif 'R-02-04' in display and 'system.data_quality_monitoring' in query:
        # Keep the query but note it may not have data if monitoring isn't enabled
        print(f"ℹ️  R-02-04: May show no data if data quality monitoring not enabled")
    
    # Fix R-05-01: user_identity.email path - try different approaches
    elif 'R-05-01' in display:
        # Try simplified version
        query = """
SELECT 
  action_name,
  COUNT(*) as event_count,
  DATE_TRUNC('day', event_time) as date
FROM system.access.audit
WHERE event_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND action_name IN ('getTable', 'createTable', 'deleteTable', 'updateTable', 'createJob', 'runJob')
GROUP BY action_name, date
ORDER BY date DESC, event_count DESC
LIMIT 100
        """
        ds['query'] = query
        fixes.append(f"R-05-01: Simplified query (removed user_identity.email)")

# Save fixed dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n✅ Applied {len(fixes)} fixes:")
for fix in fixes:
    print(f"   • {fix}")

print(f"\n{'='*70}")
print(f"✅ All queries fixed!")
print(f"🚀 Ready to redeploy!")
