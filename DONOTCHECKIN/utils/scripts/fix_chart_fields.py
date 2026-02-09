#!/usr/bin/env python3
"""
Fix Chart Field Mappings - Map encodings to actual SQL column names
"""

import json
import uuid

def generate_widget_id():
    """Generate a unique widget ID"""
    return str(uuid.uuid4())[:8]

def create_proper_widget(widget_type, title, dataset_name, dataset_info, x, y, width, height):
    """Create a widget with proper field mappings"""
    
    # Map widget types to their configurations
    if widget_type == "line":
        # Line chart for trends
        widget = {
            "name": generate_widget_id(),
            "queries": [
                {
                    "name": f"query_{generate_widget_id()}",
                    "query": {
                        "datasetName": dataset_name,
                        "fields": [
                            {"name": dataset_info["x_field"], "expression": f"`{dataset_info['x_field']}`"},
                            {"name": dataset_info["y_field"], "expression": f"`{dataset_info['y_field']}`"}
                        ]
                    }
                }
            ],
            "spec": {
                "version": 3,
                "widgetType": "line",
                "encodings": {
                    "x": {
                        "fieldName": dataset_info["x_field"],
                        "displayName": dataset_info["x_label"]
                    },
                    "y": [
                        {
                            "fieldName": dataset_info["y_field"],
                            "displayName": dataset_info["y_label"]
                        }
                    ]
                },
                "frame": {
                    "showTitle": True,
                    "title": title
                }
            }
        }
    
    elif widget_type == "bar":
        # Bar chart for comparisons
        widget = {
            "name": generate_widget_id(),
            "queries": [
                {
                    "name": f"query_{generate_widget_id()}",
                    "query": {
                        "datasetName": dataset_name,
                        "fields": [
                            {"name": dataset_info["x_field"], "expression": f"`{dataset_info['x_field']}`"},
                            {"name": dataset_info["y_field"], "expression": f"`{dataset_info['y_field']}`"}
                        ]
                    }
                }
            ],
            "spec": {
                "version": 3,
                "widgetType": "bar",
                "encodings": {
                    "x": {
                        "fieldName": dataset_info["x_field"],
                        "displayName": dataset_info["x_label"]
                    },
                    "y": [
                        {
                            "fieldName": dataset_info["y_field"],
                            "displayName": dataset_info["y_label"]
                        }
                    ]
                },
                "frame": {
                    "showTitle": True,
                    "title": title
                }
            }
        }
    
    elif widget_type == "pie":
        # Pie chart for distributions
        widget = {
            "name": generate_widget_id(),
            "queries": [
                {
                    "name": f"query_{generate_widget_id()}",
                    "query": {
                        "datasetName": dataset_name,
                        "fields": [
                            {"name": dataset_info["label_field"], "expression": f"`{dataset_info['label_field']}`"},
                            {"name": dataset_info["value_field"], "expression": f"`{dataset_info['value_field']}`"}
                        ]
                    }
                }
            ],
            "spec": {
                "version": 3,
                "widgetType": "pie",
                "encodings": {
                    "label": {
                        "fieldName": dataset_info["label_field"],
                        "displayName": dataset_info["label_label"]
                    },
                    "value": {
                        "fieldName": dataset_info["value_field"],
                        "displayName": dataset_info["value_label"]
                    }
                },
                "frame": {
                    "showTitle": True,
                    "title": title
                }
            }
        }
    
    else:  # table
        # Get all fields from dataset info
        fields = dataset_info.get("fields", [])
        widget = {
            "name": generate_widget_id(),
            "queries": [
                {
                    "name": f"query_{generate_widget_id()}",
                    "query": {
                        "datasetName": dataset_name,
                        "fields": [{"name": f, "expression": f"`{f}`"} for f in fields]
                    }
                }
            ],
            "spec": {
                "version": 3,
                "widgetType": "table",
                "encodings": {
                    "columns": [{"fieldName": f, "displayName": f.replace("_", " ").title()} for f in fields]
                },
                "frame": {
                    "showTitle": True,
                    "title": title
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

def main():
    input_file = 'dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json'
    
    print("🔧 Fixing Chart Field Mappings...")
    print("="*60)
    
    # Load dashboard
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Find the Summary page
    summary_page = None
    for page in dashboard.get('pages', []):
        if 'Summary' in page.get('displayName', ''):
            summary_page = page
            break
    
    if not summary_page:
        print("❌ Summary page not found")
        return
    
    # Find our newly added datasets
    datasets = dashboard.get('datasets', [])
    
    # Remove the broken new widgets (ones we just added)
    original_count = len(summary_page['layout'])
    
    # Keep only the original widgets (remove our broken additions)
    valid_layouts = []
    for layout in summary_page['layout']:
        widget = layout.get('widget', {})
        spec = widget.get('spec', {})
        frame = spec.get('frame', {})
        title = frame.get('title', '')
        
        # Skip our new charts (they have emojis in titles)
        if any(emoji in title for emoji in ['💰', '🔥', '📦', '⚡', '🔐', '✅', '🔍']):
            continue
        
        valid_layouts.append(layout)
    
    summary_page['layout'] = valid_layouts
    removed = original_count - len(valid_layouts)
    print(f"✅ Removed {removed} broken widgets")
    
    # Now add properly configured widgets
    max_y = 0
    for item in summary_page['layout']:
        pos = item.get('position', {})
        y = pos.get('y', 0)
        height = pos.get('height', 0)
        max_y = max(max_y, y + height)
    
    print(f"✅ Adding new charts at Y position: {max_y + 1}")
    
    # Define our chart configurations with proper field mappings
    new_charts = [
        {
            "type": "line",
            "title": "💰 Daily Cost Trend (Last 30 Days)",
            "dataset_key": "cost_trend",
            "fields": {"x_field": "date", "y_field": "daily_cost", "x_label": "Date", "y_label": "Daily Cost ($)"},
            "position": (0, max_y + 1, 6, 4)
        },
        {
            "type": "bar",
            "title": "🔥 Top 10 Most Expensive Jobs",
            "dataset_key": "expensive_jobs",
            "fields": {"x_field": "job_name", "y_field": "total_cost", "x_label": "Job Name", "y_label": "Total Cost ($)"},
            "position": (6, max_y + 1, 6, 4)
        },
        {
            "type": "line",
            "title": "📦 Storage Growth Trend (Last 90 Days)",
            "dataset_key": "storage_growth",
            "fields": {"x_field": "date", "y_field": "total_storage_gb", "x_label": "Date", "y_label": "Storage (GB)"},
            "position": (0, max_y + 5, 6, 4)
        },
        {
            "type": "pie",
            "title": "⚡ Photon Adoption Rate",
            "dataset_key": "photon_rate",
            "fields": {"label_field": "cluster_type", "value_field": "count", "label_label": "Type", "value_label": "Count"},
            "position": (6, max_y + 5, 3, 4)
        },
        {
            "type": "table",
            "title": "🔐 Unity Catalog by Schema",
            "dataset_key": "uc_by_schema",
            "fields": {"fields": ["table_schema", "table_count", "managed_tables", "external_tables"]},
            "position": (9, max_y + 5, 3, 4)
        },
        {
            "type": "pie",
            "title": "✅ Job Success Rate",
            "dataset_key": "failed_jobs",
            "fields": {"label_field": "status", "value_field": "count", "label_label": "Status", "value_label": "Count"},
            "position": (0, max_y + 9, 4, 4)
        },
        {
            "type": "table",
            "title": "🔍 Data Access Patterns (Last 7 Days)",
            "dataset_key": "access_audit",
            "fields": {"fields": ["user_email", "tables_accessed", "access_count", "last_access"]},
            "position": (4, max_y + 9, 8, 4)
        }
    ]
    
    # Find our datasets by matching keywords
    dataset_map = {}
    for ds in datasets:
        display_name = ds.get('displayName', '').lower()
        if 'cost trend' in display_name:
            dataset_map['cost_trend'] = ds['name']
        elif 'expensive jobs' in display_name:
            dataset_map['expensive_jobs'] = ds['name']
        elif 'storage growth' in display_name:
            dataset_map['storage_growth'] = ds['name']
        elif 'photon adoption' in display_name:
            dataset_map['photon_rate'] = ds['name']
        elif 'unity catalog tables' in display_name:
            dataset_map['uc_by_schema'] = ds['name']
        elif 'success vs failure' in display_name or 'job success' in display_name:
            dataset_map['failed_jobs'] = ds['name']
        elif 'data access' in display_name:
            dataset_map['access_audit'] = ds['name']
    
    # Create and add new widgets
    widgets_added = 0
    for chart_config in new_charts:
        dataset_key = chart_config["dataset_key"]
        if dataset_key in dataset_map:
            dataset_name = dataset_map[dataset_key]
            x, y, w, h = chart_config["position"]
            widget_layout = create_proper_widget(
                chart_config["type"],
                chart_config["title"],
                dataset_name,
                chart_config["fields"],
                x, y, w, h
            )
            summary_page['layout'].append(widget_layout)
            widgets_added += 1
            print(f"   ✅ Added: {chart_config['title']}")
        else:
            print(f"   ⚠️  Dataset not found for: {chart_config['title']}")
    
    # Save fixed dashboard
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Fixed dashboard saved!")
    print(f"{'='*60}")
    print(f"   Removed broken widgets: {removed}")
    print(f"   Added properly configured widgets: {widgets_added}")
    print(f"\n🚀 Ready to redeploy!")

if __name__ == "__main__":
    main()
