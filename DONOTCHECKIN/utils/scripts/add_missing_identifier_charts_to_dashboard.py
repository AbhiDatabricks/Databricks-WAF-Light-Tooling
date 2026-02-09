#!/usr/bin/env python3
"""
Add Missing WAF Identifier Charts to Dashboard
All charts comply with missing identifiers and use system tables
"""

import json
import uuid

def generate_id():
    return str(uuid.uuid4())[:8]

def create_widget(chart_config, x, y, width, height):
    """Create a widget with proper field mappings"""
    
    widget_type = chart_config['chart_type']
    fields = chart_config['fields']
    
    if widget_type == "line":
        widget = {
            "name": generate_id(),
            "queries": [{
                "name": f"query_{generate_id()}",
                "query": {
                    "datasetName": chart_config['dataset_name'],
                    "fields": [
                        {"name": fields["x_field"], "expression": f"`{fields['x_field']}`"},
                        {"name": fields["y_field"], "expression": f"`{fields['y_field']}`"}
                    ]
                }
            }],
            "spec": {
                "version": 3,
                "widgetType": "line",
                "encodings": {
                    "x": {"fieldName": fields["x_field"], "displayName": fields["x_label"]},
                    "y": [{"fieldName": fields["y_field"], "displayName": fields["y_label"]}]
                },
                "frame": {"showTitle": True, "title": chart_config['display_name']}
            }
        }
    elif widget_type == "bar":
        widget = {
            "name": generate_id(),
            "queries": [{
                "name": f"query_{generate_id()}",
                "query": {
                    "datasetName": chart_config['dataset_name'],
                    "fields": [
                        {"name": fields["x_field"], "expression": f"`{fields['x_field']}`"},
                        {"name": fields["y_field"], "expression": f"`{fields['y_field']}`"}
                    ]
                }
            }],
            "spec": {
                "version": 3,
                "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": fields["x_field"], "displayName": fields["x_label"]},
                    "y": [{"fieldName": fields["y_field"], "displayName": fields["y_label"]}]
                },
                "frame": {"showTitle": True, "title": chart_config['display_name']}
            }
        }
    else:  # pie
        widget = {
            "name": generate_id(),
            "queries": [{
                "name": f"query_{generate_id()}",
                "query": {
                    "datasetName": chart_config['dataset_name'],
                    "fields": [
                        {"name": fields["label_field"], "expression": f"`{fields['label_field']}`"},
                        {"name": fields["value_field"], "expression": f"`{fields['value_field']}`"}
                    ]
                }
            }],
            "spec": {
                "version": 3,
                "widgetType": "pie",
                "encodings": {
                    "label": {"fieldName": fields["label_field"], "displayName": fields["label_label"]},
                    "value": {"fieldName": fields["value_field"], "displayName": fields["value_label"]}
                },
                "frame": {"showTitle": True, "title": chart_config['display_name']}
            }
        }
    
    return {
        "widget": widget,
        "position": {"x": x, "y": y, "z": 0, "width": width, "height": height}
    }

def main():
    input_file = 'dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json'
    
    print("📊 Adding Missing WAF Identifier Charts to Dashboard")
    print("="*70)
    
    # Load dashboard
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Load chart definitions
    with open('DONOTCHECKIN/missing_identifier_charts.json', 'r') as f:
        chart_definitions = json.load(f)
    
    print(f"\n✅ Loaded {len(chart_definitions)} chart definitions")
    
    # Add datasets to dashboard
    if 'datasets' not in dashboard:
        dashboard['datasets'] = []
    
    new_datasets = []
    for chart in chart_definitions:
        dataset = {
            "name": chart['dataset_name'],
            "displayName": chart['display_name'],
            "query": chart['query'].strip()
        }
        new_datasets.append(dataset)
        dashboard['datasets'].append(dataset)
    
    print(f"✅ Added {len(new_datasets)} new datasets")
    
    # Group charts by pillar
    charts_by_pillar = {}
    for chart in chart_definitions:
        pillar = chart['pillar']
        if pillar not in charts_by_pillar:
            charts_by_pillar[pillar] = []
        charts_by_pillar[pillar].append(chart)
    
    print(f"\n📊 Charts by Pillar:")
    for pillar, charts in charts_by_pillar.items():
        print(f"   • {pillar}: {len(charts)} charts")
    
    # Add charts to appropriate pages
    pages = dashboard.get('pages', [])
    
    for page in pages:
        page_name = page.get('displayName', '')
        
        # Match page name to pillar
        pillar_match = None
        if 'Reliability' in page_name:
            pillar_match = 'Reliability'
        elif 'Performance' in page_name:
            pillar_match = 'Performance Efficiency'
        elif 'Cost' in page_name and 'Optimisation' in page_name:
            pillar_match = 'Cost Optimization'
        elif 'Governance' in page_name:
            pillar_match = 'Data And AI Governance'
        elif 'Security' in page_name:
            pillar_match = 'Security, Compliance and Privac'
        
        if pillar_match and pillar_match in charts_by_pillar:
            pillar_charts = charts_by_pillar[pillar_match]
            print(f"\n   Adding {len(pillar_charts)} charts to '{page_name}' page")
            
            # Get max Y position
            max_y = 0
            for item in page['layout']:
                pos = item.get('position', {})
                y = pos.get('y', 0)
                height = pos.get('height', 0)
                max_y = max(max_y, y + height)
            
            print(f"      Starting at Y position: {max_y + 1}")
            
            # Add charts (2 per row)
            for i, chart_config in enumerate(pillar_charts):
                row = i // 2
                col = i % 2
                x = col * 6
                y = max_y + 1 + (row * 5)
                
                widget_layout = create_widget(chart_config, x, y, 6, 4)
                page['layout'].append(widget_layout)
                print(f"      ✅ Added: {chart_config['display_name']}")
    
    # Save updated dashboard
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ Missing identifier charts added successfully!")
    print(f"{'='*70}")
    print(f"\nSummary:")
    for pillar, charts in charts_by_pillar.items():
        print(f"   • {pillar}: {len(charts)} charts added")
    print(f"\n🚀 Ready to deploy!")

if __name__ == "__main__":
    main()
