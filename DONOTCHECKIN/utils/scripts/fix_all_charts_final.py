#!/usr/bin/env python3
"""
Final Fix for All Charts - Ensure All Queries and Field Mappings Are Correct
"""

import json
import re

print("🔧 Final Fix for All Charts...")
print("="*70)

# Load dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

fixes = []

# Fix all new charts systematically
for page in dashboard.get('pages', []):
    for layout in page.get('layout', []):
        widget = layout.get('widget', {})
        spec = widget.get('spec', {})
        frame = spec.get('frame', {})
        title = frame.get('title', '')
        
        # Only fix our new charts
        if not any(x in title for x in ['R-01-02', 'R-01-03', 'R-01-06', 'R-02-01', 'R-02-02', 'R-02-03', 'R-02-04', 'R-02-05', 'R-04-02', 'R-04-03', 'R-05-01', 'R-05-02']):
            continue
        
        queries = widget.get('queries', [])
        if not queries:
            continue
        
        dataset_name = queries[0].get('query', {}).get('datasetName', '')
        
        # Find dataset
        dataset = None
        for ds in dashboard['datasets']:
            if ds.get('name') == dataset_name:
                dataset = ds
                break
        
        if not dataset:
            continue
        
        query = dataset.get('query', '')
        query_obj = queries[0].get('query', {})
        widget_type = spec.get('widgetType', '')
        encodings = spec.get('encodings', {})
        
        # Fix based on chart type and identifier
        if 'R-01-02' in title:
            # Pie chart: engine_type, percentage
            query_obj['fields'] = [
                {"name": "engine_type", "expression": "`engine_type`"},
                {"name": "percentage", "expression": "`percentage`"}
            ]
            if 'value' in encodings:
                encodings['value']['fieldName'] = 'percentage'
            fixes.append("R-01-02: Fixed fields and encoding")
        
        elif 'R-01-03' in title:
            # Bar chart: pipeline_name, success_rate
            query_obj['fields'] = [
                {"name": "pipeline_name", "expression": "`pipeline_name`"},
                {"name": "success_rate", "expression": "`success_rate`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'pipeline_name'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'success_rate'
            fixes.append("R-01-03: Fixed fields and encoding")
        
        elif 'R-01-06' in title:
            # Pie chart: service_type, percentage
            query_obj['fields'] = [
                {"name": "service_type", "expression": "`service_type`"},
                {"name": "percentage", "expression": "`percentage`"}
            ]
            if 'value' in encodings:
                encodings['value']['fieldName'] = 'percentage'
            fixes.append("R-01-06: Fixed fields and encoding")
        
        elif 'R-02-01' in title:
            # Pie chart: layer, table_count
            query_obj['fields'] = [
                {"name": "layer", "expression": "`layer`"},
                {"name": "table_count", "expression": "`table_count`"}
            ]
            if 'value' in encodings:
                encodings['value']['fieldName'] = 'table_count'
            fixes.append("R-02-01: Fixed fields and encoding")
        
        elif 'R-02-02' in title:
            # Bar chart: table_name, schema_count
            query_obj['fields'] = [
                {"name": "table_name", "expression": "`table_name`"},
                {"name": "schema_count", "expression": "`schema_count`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'table_name'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'schema_count'
            fixes.append("R-02-02: Fixed fields and encoding")
        
        elif 'R-02-03' in title:
            # Bar chart: table_schema, table_count
            query_obj['fields'] = [
                {"name": "table_schema", "expression": "`table_schema`"},
                {"name": "table_count", "expression": "`table_count`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'table_schema'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'table_count'
            fixes.append("R-02-03: Fixed fields and encoding")
        
        elif 'R-02-04' in title:
            # Bar chart: table_full_name, failed
            query_obj['fields'] = [
                {"name": "table_full_name", "expression": "`table_full_name`"},
                {"name": "failed", "expression": "`failed`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'table_full_name'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'failed'
            fixes.append("R-02-04: Fixed fields and encoding")
        
        elif 'R-02-05' in title:
            # Line chart: month, experiment_count
            query_obj['fields'] = [
                {"name": "month", "expression": "`month`"},
                {"name": "experiment_count", "expression": "`experiment_count`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'month'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'experiment_count'
            fixes.append("R-02-05: Fixed fields and encoding")
        
        elif 'R-04-02' in title:
            # Bar chart: table_schema, delta_tables
            query_obj['fields'] = [
                {"name": "table_schema", "expression": "`table_schema`"},
                {"name": "delta_tables", "expression": "`delta_tables`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'table_schema'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'delta_tables'
            fixes.append("R-04-02: Fixed fields and encoding")
        
        elif 'R-04-03' in title:
            # Line chart: date, success_rate
            query_obj['fields'] = [
                {"name": "date", "expression": "`date`"},
                {"name": "success_rate", "expression": "`success_rate`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'date'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'success_rate'
            fixes.append("R-04-03: Fixed fields and encoding")
        
        elif 'R-05-01' in title:
            # Bar chart: action_name, event_count
            query_obj['fields'] = [
                {"name": "action_name", "expression": "`action_name`"},
                {"name": "event_count", "expression": "`event_count`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'action_name'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'event_count'
            fixes.append("R-05-01: Fixed fields and encoding")
        
        elif 'R-05-02' in title:
            # Line chart: date, total_usage
            query_obj['fields'] = [
                {"name": "date", "expression": "`date`"},
                {"name": "total_usage", "expression": "`total_usage`"}
            ]
            if 'x' in encodings:
                encodings['x']['fieldName'] = 'date'
            if 'y' in encodings and encodings['y']:
                encodings['y'][0]['fieldName'] = 'total_usage'
            fixes.append("R-05-02: Fixed fields and encoding")

# Save
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n✅ Applied {len(fixes)} fixes:")
for fix in fixes:
    print(f"   • {fix}")

print(f"\n{'='*70}")
print(f"✅ All charts fixed!")
print(f"🚀 Ready to redeploy!")
