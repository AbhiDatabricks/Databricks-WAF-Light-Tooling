#!/usr/bin/env python3
"""
Update control table widgets for Governance, Cost, and Performance to show all columns
"""
import json

print("📊 Updating Control Table Widgets...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Dataset IDs for control tables
control_datasets = {
    '1eab9fe1': 'Governance',
    'dbdc9433': 'Cost',
    '4745a0f9': 'Performance'
}

# Fields to include in all control tables
required_fields = [
    {"name": "waf_id", "expression": "`waf_id`"},
    {"name": "principle", "expression": "`principle`"},
    {"name": "description", "expression": "`description`"},
    {"name": "score_percentage", "expression": "`score_percentage`"},
    {"name": "threshold_percentage", "expression": "`threshold_percentage`"},
    {"name": "threshold_met", "expression": "`threshold_met`"},
    {"name": "implemented", "expression": "`implemented`"}
]

# For Cost and Performance, use "best_practice" instead of "description"
cost_perf_fields = [
    {"name": "waf_id", "expression": "`waf_id`"},
    {"name": "principle", "expression": "`principle`"},
    {"name": "best_practice", "expression": "`best_practice`"},
    {"name": "score_percentage", "expression": "`score_percentage`"},
    {"name": "threshold_percentage", "expression": "`threshold_percentage`"},
    {"name": "threshold_met", "expression": "`threshold_met`"},
    {"name": "implemented", "expression": "`implemented`"}
]

def update_widgets(dashboard, dataset_id, fields):
    """Update all widgets using a specific dataset"""
    updated_count = 0
    
    def update_widget_recursive(obj):
        nonlocal updated_count
        if isinstance(obj, dict):
            # Check if this is a widget query using our dataset
            if 'queries' in obj:
                for query in obj.get('queries', []):
                    if isinstance(query, dict) and 'query' in query:
                        query_obj = query['query']
                        if query_obj.get('datasetName') == dataset_id:
                            # Update fields
                            query_obj['fields'] = fields
                            updated_count += 1
                            print(f"  ✅ Updated widget using dataset {dataset_id}")
            
            # Recursively check all values
            for value in obj.values():
                update_widget_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                update_widget_recursive(item)
    
    update_widget_recursive(dashboard)
    return updated_count

# Update each pillar
for dataset_id, pillar_name in control_datasets.items():
    print(f"\n🔧 Updating {pillar_name} control table widgets...")
    if pillar_name == 'Governance':
        count = update_widgets(dashboard, dataset_id, required_fields)
    else:
        count = update_widgets(dashboard, dataset_id, cost_perf_fields)
    print(f"  Updated {count} widget(s)")

# Save dashboard
print("\n💾 Saving dashboard...")
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ All control table widgets updated!")
print("="*70)
