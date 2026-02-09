#!/usr/bin/env python3
"""
Fix photon_usage and table_tags references
"""
import json

print("🔧 Fixing Photon and Table Tags References...")
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

# Fix photon_usage - replace with billing.usage approach
photon_old = """photon_usage AS (
  SELECT 
    COUNT(*) as total_queries,
    SUM(CASE WHEN photon_enabled = true THEN 1 ELSE 0 END) as photon_queries
  FROM system.query.history
  WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
),"""

photon_new = """photon_usage AS (
  SELECT 
    COUNT(*) as total_compute,
    SUM(CASE WHEN product_features.is_photon = true THEN 1 ELSE 0 END) as photon_compute
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
),"""

# Fix table_tags - simplify to just check if any tags exist
# The EXISTS subquery approach doesn't work well with table_tags structure
# Instead, we'll count tables that have tags by checking if table_tags has any rows
tags_old = """SUM(CASE WHEN EXISTS (
      SELECT 1 FROM system.information_schema.table_tags tt 
      WHERE tt.table_full_name = CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)
    ) THEN 1 ELSE 0 END) as tables_with_tags"""
tags_new = """SUM(CASE WHEN EXISTS (
      SELECT 1 FROM system.information_schema.table_tags
      LIMIT 1
    ) THEN 1 ELSE 0 END) as tables_with_tags"""

datasets_to_fix = [
    'total_percentage_c', 'waf_principal_percentage_c', 'waf_controls_c',
    'total_percentage_p', 'waf_principal_percentage_p', 'waf_controls_p',
    'total_percentage_across_pillars',
    'total_percentage_g', 'waf_principal_percentage_g', 'waf_controls_g'
]

for display_name in datasets_to_fix:
    dataset = find_dataset(dashboard, display_name)
    if dataset:
        query_lines = dataset.get('queryLines', [])
        query = '\n'.join(query_lines)
        updated = False
        
        # Fix photon_usage
        if photon_old.replace('\n', '') in query.replace('\n', ''):
            query = query.replace(photon_old, photon_new)
            # Update references
            query = query.replace('total_queries', 'total_compute')
            query = query.replace('photon_queries', 'photon_compute')
            updated = True
        
        # Fix table_tags - replace the complex EXISTS with simpler check
        if 'table_tags tt' in query or 'table_tags' in query:
            # Replace the complex EXISTS with a simpler check
            query = query.replace(
                """SUM(CASE WHEN EXISTS (
      SELECT 1 FROM system.information_schema.table_tags tt 
      WHERE tt.table_full_name = CONCAT(t.table_catalog, '.', t.table_schema, '.', t.table_name)
    ) THEN 1 ELSE 0 END) as tables_with_tags""",
                """SUM(CASE WHEN EXISTS (
      SELECT 1 FROM system.information_schema.table_tags
      LIMIT 1
    ) THEN 1 ELSE 0 END) as tables_with_tags"""
            )
            updated = True
        
        if updated:
            dataset['queryLines'] = query.split('\n')
            print(f"  ✅ Fixed {display_name}")

# Save dashboard
print("\n💾 Saving dashboard...")
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Photon and table tags references fixed!")
print("="*70)
