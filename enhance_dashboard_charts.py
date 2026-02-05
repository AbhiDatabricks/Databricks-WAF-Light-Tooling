#!/usr/bin/env python3
"""
Enhance WAF Dashboard - Add Missing Charts and Fix Rendering Issues
"""

import json
import uuid
from copy import deepcopy

def generate_widget_id():
    """Generate a unique widget ID"""
    return str(uuid.uuid4())[:8]

def add_new_datasets(dashboard):
    """Add new useful datasets for WAF assessment"""
    
    new_datasets = []
    
    # 1. Cost Trend Over Time (30 days)
    new_datasets.append({
        "name": f"cost_trend_{generate_widget_id()}",
        "displayName": "Cost Trend (Last 30 Days)",
        "query": """
SELECT 
  DATE_TRUNC('day', usage_start_time) as date,
  SUM(usage_quantity * list_price) as daily_cost,
  workspace_id
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date, workspace_id
ORDER BY date DESC
        """
    })
    
    # 2. Top 10 Most Expensive Jobs
    new_datasets.append({
        "name": f"expensive_jobs_{generate_widget_id()}",
        "displayName": "Top 10 Most Expensive Jobs",
        "query": """
SELECT 
  job_name,
  SUM(usage_quantity * list_price) as total_cost,
  COUNT(*) as run_count,
  AVG(usage_quantity * list_price) as avg_cost_per_run
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '7' DAY
  AND usage_type = 'JOBS'
GROUP BY job_name
ORDER BY total_cost DESC
LIMIT 10
        """
    })
    
    # 3. Storage Growth Trend
    new_datasets.append({
        "name": f"storage_growth_{generate_widget_id()}",
        "displayName": "Storage Growth Trend",
        "query": """
SELECT 
  DATE_TRUNC('day', usage_start_time) as date,
  SUM(usage_quantity) as total_storage_gb,
  workspace_id
FROM system.billing.usage
WHERE usage_type LIKE '%STORAGE%'
  AND usage_start_time >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY date, workspace_id
ORDER BY date DESC
        """
    })
    
    # 4. Failed Jobs Rate
    new_datasets.append({
        "name": f"failed_jobs_{generate_widget_id()}",
        "displayName": "Job Success vs Failure Rate",
        "query": """
SELECT 
  CASE 
    WHEN state = 'SUCCESS' THEN 'Success'
    WHEN state IN ('FAILED', 'TIMEDOUT', 'CANCELED') THEN 'Failed'
    ELSE 'Other'
  END as status,
  COUNT(*) as count
FROM system.compute.clusters c
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY status
        """
    })
    
    # 5. Unity Catalog Adoption by Schema
    new_datasets.append({
        "name": f"uc_by_schema_{generate_widget_id()}",
        "displayName": "Unity Catalog Tables by Schema",
        "query": """
SELECT 
  table_schema,
  COUNT(*) as table_count,
  SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END) as managed_tables,
  SUM(CASE WHEN table_type = 'EXTERNAL' THEN 1 ELSE 0 END) as external_tables
FROM system.information_schema.tables
WHERE table_catalog != 'hive_metastore'
GROUP BY table_schema
ORDER BY table_count DESC
LIMIT 20
        """
    })
    
    # 6. Cluster Utilization by Type
    new_datasets.append({
        "name": f"cluster_util_{generate_widget_id()}",
        "displayName": "Cluster Utilization by Type",
        "query": """
SELECT 
  cluster_type,
  AVG(DATEDIFF(SECOND, start_time, end_time) / 3600.0) as avg_runtime_hours,
  COUNT(*) as cluster_count
FROM system.compute.clusters
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY cluster_type
        """
    })
    
    # 7. Security - Data Access Audit
    new_datasets.append({
        "name": f"access_audit_{generate_widget_id()}",
        "displayName": "Recent Data Access Patterns",
        "query": """
SELECT 
  user_identity.email as user_email,
  COUNT(DISTINCT request_params.table_full_name) as tables_accessed,
  COUNT(*) as access_count,
  MAX(event_time) as last_access
FROM system.access.audit
WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
  AND action_name = 'getTable'
GROUP BY user_email
ORDER BY access_count DESC
LIMIT 50
        """
    })
    
    # 8. Photon Adoption Rate
    new_datasets.append({
        "name": f"photon_rate_{generate_widget_id()}",
        "displayName": "Photon Adoption Rate",
        "query": """
SELECT 
  CASE WHEN photon_enabled = true THEN 'Photon Enabled' ELSE 'Standard' END as cluster_type,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.compute.clusters
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY photon_enabled
        """
    })
    
    return new_datasets

def create_widget(widget_type, title, dataset_name, x, y, width, height):
    """Create a widget with proper structure"""
    
    widget_templates = {
        "counter": {
            "widgetType": "counter",
            "encodings": {
                "value": {
                    "fieldName": "count",
                    "displayName": "Count"
                }
            }
        },
        "line": {
            "widgetType": "line",
            "encodings": {
                "x": {
                    "fieldName": "date",
                    "displayName": "Date"
                },
                "y": [
                    {
                        "fieldName": "value",
                        "displayName": "Value"
                    }
                ]
            }
        },
        "bar": {
            "widgetType": "bar",
            "encodings": {
                "x": {
                    "fieldName": "category",
                    "displayName": "Category"
                },
                "y": [
                    {
                        "fieldName": "value",
                        "displayName": "Value"
                    }
                ]
            }
        },
        "pie": {
            "widgetType": "pie",
            "encodings": {
                "label": {
                    "fieldName": "category",
                    "displayName": "Category"
                },
                "value": {
                    "fieldName": "value",
                    "displayName": "Value"
                }
            }
        },
        "table": {
            "widgetType": "table",
            "encodings": {
                "columns": []
            }
        }
    }
    
    widget = {
        "name": generate_widget_id(),
        "queries": [
            {
                "name": f"query_{generate_widget_id()}",
                "query": {
                    "datasetName": dataset_name,
                    "fields": []
                }
            }
        ],
        "spec": {
            **widget_templates.get(widget_type, widget_templates["table"]),
            "frame": {
                "showTitle": True,
                "title": title,
                "showDescription": False
            }
        }
    }
    
    layout = {
        "widget": widget,
        "position": {
            "x": x,
            "y": y,
            "z": 0,
            "width": width,
            "height": height
        }
    }
    
    return layout

def fix_missing_titles(dashboard):
    """Add titles to widgets that are missing them"""
    
    default_titles = {
        "counter": "Metric Count",
        "pie": "Distribution",
        "bar": "Comparison",
        "line": "Trend",
        "table": "Details"
    }
    
    fixed_count = 0
    
    for page in dashboard.get('pages', []):
        for layout_item in page.get('layout', []):
            widget = layout_item.get('widget', {})
            spec = widget.get('spec', {})
            frame = spec.get('frame', {})
            widget_type = spec.get('widgetType', 'unknown')
            
            # Fix missing titles
            if widget_type != 'text' and not frame.get('title'):
                if widget_type in default_titles:
                    if 'frame' not in spec:
                        spec['frame'] = {}
                    spec['frame']['title'] = default_titles[widget_type]
                    spec['frame']['showTitle'] = True
                    fixed_count += 1
    
    return fixed_count

def add_new_visualizations(dashboard):
    """Add new chart visualizations to the dashboard"""
    
    # Add new datasets first
    new_datasets = add_new_datasets(dashboard)
    if 'datasets' not in dashboard:
        dashboard['datasets'] = []
    
    dashboard['datasets'].extend(new_datasets)
    
    # Find the Summary page to add overview charts
    summary_page = None
    for page in dashboard.get('pages', []):
        if 'Summary' in page.get('displayName', ''):
            summary_page = page
            break
    
    if not summary_page:
        return 0
    
    # Get current max Y position to add new widgets below
    max_y = 0
    for item in summary_page.get('layout', []):
        pos = item.get('position', {})
        y = pos.get('y', 0)
        height = item.get('size', {}).get('height', 0)
        max_y = max(max_y, y + height)
    
    new_widgets = []
    
    # Add Cost Trend Chart (Line Chart)
    cost_dataset = next((ds for ds in new_datasets if 'Cost Trend' in ds['displayName']), None)
    if cost_dataset:
        new_widgets.append(create_widget(
            "line",
            "💰 Daily Cost Trend (Last 30 Days)",
            cost_dataset['name'],
            0, max_y + 1, 6, 4
        ))
    
    # Add Expensive Jobs Chart (Bar Chart)
    jobs_dataset = next((ds for ds in new_datasets if 'Most Expensive Jobs' in ds['displayName']), None)
    if jobs_dataset:
        new_widgets.append(create_widget(
            "bar",
            "🔥 Top 10 Most Expensive Jobs (Last 7 Days)",
            jobs_dataset['name'],
            6, max_y + 1, 6, 4
        ))
    
    # Add Storage Growth (Line Chart)
    storage_dataset = next((ds for ds in new_datasets if 'Storage Growth' in ds['displayName']), None)
    if storage_dataset:
        new_widgets.append(create_widget(
            "line",
            "📦 Storage Growth Trend (Last 90 Days)",
            storage_dataset['name'],
            0, max_y + 5, 6, 4
        ))
    
    # Add Photon Adoption (Pie Chart)
    photon_dataset = next((ds for ds in new_datasets if 'Photon Adoption' in ds['displayName']), None)
    if photon_dataset:
        new_widgets.append(create_widget(
            "pie",
            "⚡ Photon Adoption Rate",
            photon_dataset['name'],
            6, max_y + 5, 3, 4
        ))
    
    # Add UC Adoption by Schema (Table)
    uc_dataset = next((ds for ds in new_datasets if 'Unity Catalog Tables' in ds['displayName']), None)
    if uc_dataset:
        new_widgets.append(create_widget(
            "table",
            "🔐 Unity Catalog Adoption by Schema",
            uc_dataset['name'],
            9, max_y + 5, 3, 4
        ))
    
    # Add Failed Jobs Rate (Pie Chart)
    failed_dataset = next((ds for ds in new_datasets if 'Success vs Failure' in ds['displayName']), None)
    if failed_dataset:
        new_widgets.append(create_widget(
            "pie",
            "✅ Job Success Rate",
            failed_dataset['name'],
            0, max_y + 9, 4, 4
        ))
    
    # Add Access Audit (Table)
    audit_dataset = next((ds for ds in new_datasets if 'Data Access Patterns' in ds['displayName']), None)
    if audit_dataset:
        new_widgets.append(create_widget(
            "table",
            "🔍 Recent Data Access Patterns (Last 7 Days)",
            audit_dataset['name'],
            4, max_y + 9, 8, 4
        ))
    
    # Add widgets to the summary page
    summary_page['layout'].extend(new_widgets)
    
    return len(new_widgets)

def main():
    input_file = 'dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json'
    output_file = input_file  # Overwrite the same file
    
    print("📊 Enhancing WAF Dashboard...")
    print("="*60)
    
    # Load dashboard
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Create backup
    backup_file = input_file + '.backup2'
    with open(backup_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"✅ Backup created: {backup_file}")
    
    # Fix missing titles
    print("\n🔧 Fixing missing widget titles...")
    fixed_titles = fix_missing_titles(dashboard)
    print(f"✅ Fixed {fixed_titles} widgets with missing titles")
    
    # Add new visualizations
    print("\n📈 Adding new visualizations...")
    new_charts = add_new_visualizations(dashboard)
    print(f"✅ Added {new_charts} new charts")
    
    # Save enhanced dashboard
    with open(output_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Enhanced dashboard saved to: {output_file}")
    print("\n📊 New Charts Added:")
    print("   1. 💰 Daily Cost Trend (Last 30 Days) - Line Chart")
    print("   2. 🔥 Top 10 Most Expensive Jobs - Bar Chart")
    print("   3. 📦 Storage Growth Trend - Line Chart")
    print("   4. ⚡ Photon Adoption Rate - Pie Chart")
    print("   5. 🔐 Unity Catalog by Schema - Table")
    print("   6. ✅ Job Success Rate - Pie Chart")
    print("   7. 🔍 Data Access Patterns - Table")
    
    print("\n🚀 Ready to deploy!")

if __name__ == "__main__":
    main()
