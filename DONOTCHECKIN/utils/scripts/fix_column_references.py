#!/usr/bin/env python3
"""
Fix column references in queries:
1. Fix table_full_name - needs to be constructed from table_catalog, table_schema, table_name
2. Verify photon_enabled exists (it should, but let's check the actual usage)
"""
import json
import re

print("🔧 Fixing Column References...")
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

def fix_lineage_usage_query(query_lines):
    """Fix lineage_usage CTE to properly construct table_full_name"""
    query = '\n'.join(query_lines)
    
    # Fix: Construct table_full_name from catalog, schema, name
    # Old: COUNT(DISTINCT t.table_full_name)
    # New: COUNT(DISTINCT CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name))
    
    query = re.sub(
        r'COUNT\(DISTINCT t\.table_full_name\)',
        r"COUNT(DISTINCT CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name))",
        query
    )
    
    query = re.sub(
        r'COUNT\(DISTINCT CASE WHEN tl\.target_table_full_name IS NOT NULL THEN t\.table_full_name END\)',
        r"COUNT(DISTINCT CASE WHEN tl.target_table_full_name IS NOT NULL THEN CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) END)",
        query
    )
    
    query = re.sub(
        r'LEFT JOIN system\.access\.table_lineage tl ON t\.table_full_name = tl\.target_table_full_name',
        r"LEFT JOIN system.access.table_lineage tl ON CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) = tl.target_table_full_name",
        query
    )
    
    return query.split('\n')

def fix_metadata_usage_query(query_lines):
    """Fix metadata_usage CTE to properly construct table_full_name"""
    query = '\n'.join(query_lines)
    
    # Fix table_tags join
    query = re.sub(
        r'WHERE tt\.table_full_name = t\.table_full_name',
        r"WHERE CONCAT(tt.table_catalog, '.', tt.table_schema, '.', tt.table_name) = CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)",
        query
    )
    
    return query.split('\n')

# Fix Governance queries
print("\n🔧 Fixing Governance queries...")
for display_name in ['total_percentage_g', 'waf_principal_percentage_g', 'waf_controls_g']:
    dataset = find_dataset(dashboard, display_name)
    if dataset:
        query_lines = dataset.get('queryLines', [])
        query = '\n'.join(query_lines)
        
        # Fix lineage_usage
        if 'lineage_usage AS (' in query:
            query = re.sub(
                r'COUNT\(DISTINCT t\.table_full_name\)',
                r"COUNT(DISTINCT CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name))",
                query
            )
            query = re.sub(
                r'COUNT\(DISTINCT CASE WHEN tl\.target_table_full_name IS NOT NULL THEN t\.table_full_name END\)',
                r"COUNT(DISTINCT CASE WHEN tl.target_table_full_name IS NOT NULL THEN CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) END)",
                query
            )
            query = re.sub(
                r'LEFT JOIN system\.access\.table_lineage tl ON t\.table_full_name = tl\.target_table_full_name',
                r"LEFT JOIN system.access.table_lineage tl ON CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) = tl.target_table_full_name",
                query
            )
        
        # Fix metadata_usage
        if 'metadata_usage AS (' in query:
            query = re.sub(
                r'WHERE tt\.table_full_name = t\.table_full_name',
                r"WHERE CONCAT(tt.table_catalog, '.', tt.table_schema, '.', tt.table_name) = CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)",
                query
            )
        
        dataset['queryLines'] = query.split('\n')
        print(f"  ✅ Fixed {display_name}")

# Fix Summary query
print("\n🔧 Fixing Summary query...")
dataset = find_dataset(dashboard, 'total_percentage_across_pillars')
if dataset:
    query_lines = dataset.get('queryLines', [])
    query = '\n'.join(query_lines)
    
    # Fix lineage_usage
    if 'lineage_usage AS (' in query:
        query = re.sub(
            r'COUNT\(DISTINCT t\.table_full_name\)',
            r"COUNT(DISTINCT CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name))",
            query
        )
        query = re.sub(
            r'COUNT\(DISTINCT CASE WHEN tl\.target_table_full_name IS NOT NULL THEN t\.table_full_name END\)',
            r"COUNT(DISTINCT CASE WHEN tl.target_table_full_name IS NOT NULL THEN CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) END)",
            query
        )
        query = re.sub(
            r'LEFT JOIN system\.access\.table_lineage tl ON t\.table_full_name = tl\.target_table_full_name',
            r"LEFT JOIN system.access.table_lineage tl ON CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name) = tl.target_table_full_name",
            query
        )
    
    # Fix metadata_usage
    if 'metadata_usage AS (' in query:
        query = re.sub(
            r'WHERE tt\.table_full_name = t\.table_full_name',
            r"WHERE CONCAT(tt.table_catalog, '.', tt.table_schema, '.', tt.table_name) = CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)",
            query
        )
    
    dataset['queryLines'] = query.split('\n')
    print(f"  ✅ Fixed total_percentage_across_pillars")

# Fix photon_usage - use system.billing.usage instead of system.query.history
print("\n🔧 Fixing Photon usage queries...")
for display_name in ['total_percentage_c', 'waf_principal_percentage_c', 'waf_controls_c', 
                     'total_percentage_p', 'waf_principal_percentage_p', 'waf_controls_p',
                     'total_percentage_across_pillars']:
    dataset = find_dataset(dashboard, display_name)
    if dataset:
        query_lines = dataset.get('queryLines', [])
        query = '\n'.join(query_lines)
        
        # Replace photon_usage CTE to use billing.usage instead
        old_photon_cte = r'photon_usage AS \(\s+SELECT\s+COUNT\(\*\) as total_queries,\s+SUM\(CASE WHEN photon_enabled = true THEN 1 ELSE 0 END\) as photon_queries\s+FROM system\.query\.history\s+WHERE start_time >= CURRENT_DATE - INTERVAL \'30\' DAY\s+\),'
        
        new_photon_cte = """photon_usage AS (
  SELECT 
    COUNT(*) as total_compute,
    SUM(CASE WHEN product_features.is_photon = true THEN 1 ELSE 0 END) as photon_compute
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
),"""
        
        query = re.sub(
            r'photon_usage AS \(\s+SELECT\s+COUNT\(\*\) as total_queries,\s+SUM\(CASE WHEN photon_enabled = true THEN 1 ELSE 0 END\) as photon_queries\s+FROM system\.query\.history\s+WHERE start_time >= CURRENT_DATE - INTERVAL \'30\' DAY\s+\),',
            new_photon_cte,
            query,
            flags=re.DOTALL
        )
        
        # Update references from total_queries/photon_queries to total_compute/photon_compute
        query = re.sub(r'total_queries', 'total_compute', query)
        query = re.sub(r'photon_queries', 'photon_compute', query)
        
        dataset['queryLines'] = query.split('\n')
        print(f"  ✅ Fixed {display_name}")

# Fix metadata_usage - table_tags might have different structure
print("\n🔧 Fixing metadata_usage table_tags join...")
for display_name in ['total_percentage_g', 'waf_principal_percentage_g', 'waf_controls_g', 'total_percentage_across_pillars']:
    dataset = find_dataset(dashboard, display_name)
    if dataset:
        query_lines = dataset.get('queryLines', [])
        query = '\n'.join(query_lines)
        
        # Fix: table_tags might not have table_catalog, table_schema, table_name
        # Use EXISTS with table_full_name instead
        query = re.sub(
            r'SUM\(CASE WHEN EXISTS \(\s+SELECT 1 FROM system\.information_schema\.table_tags tt\s+WHERE CONCAT\(tt\.table_catalog, \'\.\', tt\.table_schema, \'\.\', tt\.table_name\) = CONCAT\(t\.table_catalog, \'\.\', t\.table_schema, \'\.\', t\.table_name\)\s+\) THEN 1 ELSE 0 END\)',
            r"SUM(CASE WHEN EXISTS (SELECT 1 FROM system.information_schema.table_tags tt WHERE tt.table_full_name = CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)) THEN 1 ELSE 0 END)",
            query,
            flags=re.DOTALL
        )
        
        dataset['queryLines'] = query.split('\n')
        if 'table_tags' in query:
            print(f"  ✅ Fixed {display_name}")

# Save dashboard
print("\n💾 Saving dashboard...")
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Column references fixed!")
print("="*70)
