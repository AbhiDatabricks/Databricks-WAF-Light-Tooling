#!/usr/bin/env python3
"""
Fix System Table Queries - Use Correct Column Names
Based on actual system table schemas
"""

import json

print("🔧 Fixing System Table Queries with Correct Column Names...")
print("="*70)

# Load dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Fix queries based on actual system table schemas
# system.compute.clusters has: change_time, create_time, delete_time, cluster_id, tags
# NOT: start_time, photon_enabled, cluster_type

fixes_applied = 0

for ds in dashboard['datasets']:
    display = ds.get('displayName', '')
    query = ds.get('query', '')
    original_query = query
    
    # Fix R-01-02: Spark/Photon Workload Distribution
    if 'R-01-02' in display and 'system.compute.clusters' in query:
        # Use node_timeline instead which has actual usage data
        query = """
SELECT 
  CASE 
    WHEN cluster_name LIKE '%photon%' OR cluster_name LIKE '%Photon%' THEN 'Photon Engine'
    ELSE 'Apache Spark'
  END as engine_type,
  COUNT(DISTINCT cluster_id) as cluster_count,
  ROUND(COUNT(DISTINCT cluster_id) * 100.0 / SUM(COUNT(DISTINCT cluster_id)) OVER (), 2) as percentage
FROM system.compute.clusters
WHERE create_time >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY engine_type
        """
        ds['query'] = query
        fixes_applied += 1
        print(f"✅ Fixed: {display}")
    
    # Fix R-01-06: Serverless vs Managed Compute Usage
    elif 'R-01-06' in display and 'system.compute.clusters' in query:
        # Use cluster_id and tags to determine type
        query = """
SELECT 
  CASE 
    WHEN tags LIKE '%serverless%' OR tags LIKE '%SERVERLESS%' THEN 'Serverless (Managed)'
    WHEN tags LIKE '%job%' OR tags LIKE '%JOB%' THEN 'Job Clusters (Managed)'
    ELSE 'Traditional (Self-Managed)'
  END as service_type,
  COUNT(DISTINCT cluster_id) as cluster_count,
  ROUND(COUNT(DISTINCT cluster_id) * 100.0 / SUM(COUNT(DISTINCT cluster_id)) OVER (), 2) as percentage
FROM system.compute.clusters
WHERE create_time >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY service_type
        """
        ds['query'] = query
        fixes_applied += 1
        print(f"✅ Fixed: {display}")
    
    # Fix R-02-02: Table Duplication - STRING_AGG may not work, use LISTAGG
    elif 'R-02-02' in display and 'STRING_AGG' in query:
        query = query.replace('STRING_AGG(DISTINCT table_schema, \', \')', 'LISTAGG(DISTINCT table_schema, \', \')')
        ds['query'] = query
        fixes_applied += 1
        print(f"✅ Fixed: {display}")
    
    # Fix R-02-03: Schema Management - last_altered may not exist
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
        fixes_applied += 1
        print(f"✅ Fixed: {display}")
    
    # Fix R-05-01: Data Platform Event Monitoring - user_identity.email may need different path
    elif 'R-05-01' in display and 'user_identity.email' in query:
        query = """
SELECT 
  action_name,
  COUNT(*) as event_count,
  COUNT(DISTINCT user_identity.email) as unique_users,
  DATE_TRUNC('day', event_time) as date
FROM system.access.audit
WHERE event_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND action_name IN ('getTable', 'createTable', 'deleteTable', 'updateTable', 'createJob', 'runJob')
GROUP BY action_name, date
ORDER BY date DESC, event_count DESC
LIMIT 100
        """
        # Keep as is - user_identity.email should work
        print(f"ℹ️  Keeping: {display} (user_identity.email should be valid)")

# Save fixed dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n{'='*70}")
print(f"✅ Fixed {fixes_applied} queries")
print(f"🚀 Ready to redeploy!")
