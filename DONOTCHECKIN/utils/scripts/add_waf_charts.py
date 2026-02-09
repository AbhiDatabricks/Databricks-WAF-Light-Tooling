#!/usr/bin/env python3
"""
Add WAF-Based Charts with Databricks Solutions
Based on identifiers from the WAF Excel file
"""

import json
import uuid

def generate_id():
    return str(uuid.uuid4())[:8]

def create_datasets_and_charts():
    """Create datasets and chart configurations based on WAF identifiers"""
    
    # Define new datasets mapped to WAF identifiers
    datasets = [
        # RELIABILITY Charts (R-*)
        {
            "name": f"waf_r_01_01_{generate_id()}",
            "displayName": "R-01-01: Delta Lake Usage",
            "waf_id": "R-01-01",
            "recommendation": "Use a data format that supports ACID transactions",
            "databricks_solution": "Delta Lake",
            "query": """
SELECT 
  table_catalog,
  table_schema,
  COUNT(*) as table_count,
  SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END) as delta_tables,
  ROUND(SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as delta_adoption_percent
FROM system.information_schema.tables
WHERE table_catalog != 'hive_metastore'
GROUP BY table_catalog, table_schema
ORDER BY table_count DESC
LIMIT 20
            """
        },
        {
            "name": f"waf_r_01_04_{generate_id()}",
            "displayName": "R-01-04: Jobs with Auto-Retry Configured",
            "waf_id": "R-01-04",
            "recommendation": "Configure jobs for automatic retries and termination",
            "databricks_solution": "Databricks Workflows",
            "query": """
SELECT 
  CASE 
    WHEN max_retries > 0 THEN 'Auto-Retry Enabled'
    ELSE 'No Auto-Retry'
  END as retry_status,
  COUNT(DISTINCT job_id) as job_count
FROM system.lakeflow.jobs
GROUP BY retry_status
            """
        },
        {
            "name": f"waf_r_03_01_{generate_id()}",
            "displayName": "R-03-01: Clusters with Autoscaling",
            "waf_id": "R-03-01",
            "recommendation": "Enable autoscaling for ETL workloads",
            "databricks_solution": "Databricks Autoscaling",
            "query": """
SELECT 
  CASE 
    WHEN autoscale_enabled = true THEN 'Autoscaling Enabled'
    ELSE 'Fixed Size'
  END as scaling_type,
  COUNT(*) as cluster_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.compute.clusters
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY autoscale_enabled
            """
        },
        {
            "name": f"waf_r_04_01_{generate_id()}",
            "displayName": "R-04-01: Streaming Query Status",
            "waf_id": "R-04-01",
            "recommendation": "Recover from Structured Streaming query failures",
            "databricks_solution": "Structured Streaming with Checkpointing",
            "query": """
SELECT 
  CASE 
    WHEN state = 'SUCCEEDED' THEN 'Running Successfully'
    WHEN state IN ('FAILED', 'TIMEDOUT') THEN 'Failed/Timeout'
    ELSE 'Other'
  END as stream_status,
  COUNT(*) as count
FROM system.compute.clusters
WHERE cluster_type = 'STREAMING'
  AND start_time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY stream_status
            """
        },
        
        # PERFORMANCE EFFICIENCY Charts (PE-*)
        {
            "name": f"waf_pe_01_01_{generate_id()}",
            "displayName": "PE-01-01: Serverless Adoption",
            "waf_id": "PE-01-01",
            "recommendation": "Use serverless architecture",
            "databricks_solution": "Databricks Serverless Compute",
            "query": """
SELECT 
  CASE 
    WHEN cluster_type = 'SERVERLESS' THEN 'Serverless'
    ELSE 'Traditional Cluster'
  END as compute_type,
  COUNT(*) as workload_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.compute.clusters
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY compute_type
            """
        },
        {
            "name": f"waf_pe_02_05_{generate_id()}",
            "displayName": "PE-02-05: Native Spark Operations Usage",
            "waf_id": "PE-02-05",
            "recommendation": "Use native Spark operations",
            "databricks_solution": "Apache Spark",
            "query": """
SELECT 
  CASE 
    WHEN udf_count > 0 THEN 'Using UDFs (Slower)'
    ELSE 'Native Operations Only'
  END as operation_type,
  COUNT(*) as query_count
FROM (
  SELECT 
    query_id,
    SUM(CASE WHEN metric_name LIKE '%udf%' THEN 1 ELSE 0 END) as udf_count
  FROM system.query.history
  WHERE start_time >= CURRENT_DATE - INTERVAL '7' DAY
  GROUP BY query_id
)
GROUP BY operation_type
            """
        },
        {
            "name": f"waf_pe_02_08_{generate_id()}",
            "displayName": "PE-02-08: Delta Caching Effectiveness",
            "waf_id": "PE-02-08",
            "recommendation": "Use caching",
            "databricks_solution": "Delta Cache",
            "query": """
SELECT 
  DATE_TRUNC('day', event_time) as date,
  SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) as cache_hits,
  SUM(CASE WHEN cache_hit = false THEN 1 ELSE 0 END) as cache_misses,
  ROUND(SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as cache_hit_rate
FROM system.query.history
WHERE event_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC
            """
        },
        
        # COST OPTIMIZATION Charts (CO-*)
        {
            "name": f"waf_co_01_02_{generate_id()}",
            "displayName": "CO-01-02: Job vs All-Purpose Cluster Usage",
            "waf_id": "CO-01-02",
            "recommendation": "Use job clusters",
            "databricks_solution": "Databricks Workflows",
            "query": """
SELECT 
  CASE 
    WHEN cluster_type = 'JOB' THEN 'Job Clusters (Cost Effective)'
    WHEN cluster_type = 'ALL_PURPOSE' THEN 'All-Purpose (Expensive)'
    ELSE 'Other'
  END as cluster_category,
  COUNT(*) as usage_count,
  ROUND(SUM(usage_quantity * list_price), 2) as total_cost
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND usage_type LIKE '%COMPUTE%'
GROUP BY cluster_category
ORDER BY total_cost DESC
            """
        },
        {
            "name": f"waf_co_01_06_{generate_id()}",
            "displayName": "CO-01-06: Serverless Cost Efficiency",
            "waf_id": "CO-01-06",
            "recommendation": "Use Serverless for your workloads",
            "databricks_solution": "Databricks Serverless",
            "query": """
SELECT 
  CASE 
    WHEN usage_type LIKE '%SERVERLESS%' THEN 'Serverless'
    ELSE 'Traditional'
  END as compute_type,
  ROUND(SUM(usage_quantity * list_price), 2) as total_cost,
  ROUND(AVG(usage_quantity * list_price), 2) as avg_cost_per_workload
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND usage_type LIKE '%COMPUTE%'
GROUP BY compute_type
            """
        },
        {
            "name": f"waf_co_01_09_{generate_id()}",
            "displayName": "CO-01-09: Photon vs Standard Performance Cost",
            "waf_id": "CO-01-09",
            "recommendation": "Evaluate performance optimized query engines",
            "databricks_solution": "Photon Engine",
            "query": """
SELECT 
  CASE 
    WHEN photon_enabled = true THEN 'Photon (3x Faster)'
    ELSE 'Standard Engine'
  END as engine_type,
  COUNT(*) as query_count,
  AVG(execution_duration_ms / 1000.0) as avg_duration_seconds,
  ROUND(SUM(usage_quantity * list_price), 2) as total_cost
FROM system.query.history q
JOIN system.billing.usage u ON q.workspace_id = u.workspace_id
WHERE q.start_time >= CURRENT_DATE - INTERVAL '7' DAY
  AND u.usage_start_time >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY engine_type
            """
        },
        {
            "name": f"waf_co_02_01_{generate_id()}",
            "displayName": "CO-02-01: Auto-Termination Savings",
            "waf_id": "CO-02-01",
            "recommendation": "Leverage auto-termination to reduce idle costs",
            "databricks_solution": "Cluster Auto-Termination",
            "query": """
SELECT 
  CASE 
    WHEN auto_termination_minutes > 0 THEN 'Auto-Terminate Enabled'
    ELSE 'No Auto-Terminate'
  END as termination_status,
  COUNT(DISTINCT cluster_id) as cluster_count,
  AVG(DATEDIFF(MINUTE, start_time, end_time)) as avg_runtime_minutes,
  ROUND(SUM(CASE WHEN state = 'RUNNING' AND DATEDIFF(MINUTE, start_time, CURRENT_TIMESTAMP) > 60 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as idle_cluster_percent
FROM system.compute.clusters
WHERE start_time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY termination_status
            """
        }
    ]
    
    # Define chart configurations
    charts = [
        # RELIABILITY Charts
        {
            "dataset_key": "waf_r_01_01",
            "title": "R-01-01: Delta Lake Adoption by Schema",
            "type": "bar",
            "fields": {"x_field": "table_schema", "y_field": "delta_adoption_percent", "x_label": "Schema", "y_label": "Delta Adoption %"},
            "pillar": "Reliability"
        },
        {
            "dataset_key": "waf_r_01_04",
            "title": "R-01-04: Job Auto-Retry Configuration",
            "type": "pie",
            "fields": {"label_field": "retry_status", "value_field": "job_count", "label_label": "Status", "value_label": "Jobs"},
            "pillar": "Reliability"
        },
        {
            "dataset_key": "waf_r_03_01",
            "title": "R-03-01: Cluster Autoscaling Adoption",
            "type": "pie",
            "fields": {"label_field": "scaling_type", "value_field": "percentage", "label_label": "Type", "value_label": "Percentage"},
            "pillar": "Reliability"
        },
        {
            "dataset_key": "waf_r_04_01",
            "title": "R-04-01: Streaming Job Health",
            "type": "pie",
            "fields": {"label_field": "stream_status", "value_field": "count", "label_label": "Status", "value_label": "Count"},
            "pillar": "Reliability"
        },
        
        # PERFORMANCE Charts
        {
            "dataset_key": "waf_pe_01_01",
            "title": "PE-01-01: Serverless Adoption Rate",
            "type": "pie",
            "fields": {"label_field": "compute_type", "value_field": "percentage", "label_label": "Type", "value_label": "Percentage"},
            "pillar": "Performance Efficiency"
        },
        {
            "dataset_key": "waf_pe_02_05",
            "title": "PE-02-05: Native Spark vs UDF Usage",
            "type": "pie",
            "fields": {"label_field": "operation_type", "value_field": "query_count", "label_label": "Operation", "value_label": "Queries"},
            "pillar": "Performance Efficiency"
        },
        {
            "dataset_key": "waf_pe_02_08",
            "title": "PE-02-08: Delta Cache Hit Rate (30 Days)",
            "type": "line",
            "fields": {"x_field": "date", "y_field": "cache_hit_rate", "x_label": "Date", "y_label": "Cache Hit Rate %"},
            "pillar": "Performance Efficiency"
        },
        
        # COST OPTIMIZATION Charts
        {
            "dataset_key": "waf_co_01_02",
            "title": "CO-01-02: Job vs All-Purpose Cluster Costs",
            "type": "bar",
            "fields": {"x_field": "cluster_category", "y_field": "total_cost", "x_label": "Cluster Type", "y_label": "Total Cost ($)"},
            "pillar": "Cost Optimisation"
        },
        {
            "dataset_key": "waf_co_01_06",
            "title": "CO-01-06: Serverless vs Traditional Cost",
            "type": "bar",
            "fields": {"x_field": "compute_type", "y_field": "avg_cost_per_workload", "x_label": "Compute Type", "y_label": "Avg Cost per Workload ($)"},
            "pillar": "Cost Optimisation"
        },
        {
            "dataset_key": "waf_co_01_09",
            "title": "CO-01-09: Photon Performance & Cost",
            "type": "bar",
            "fields": {"x_field": "engine_type", "y_field": "avg_duration_seconds", "x_label": "Engine", "y_label": "Avg Duration (seconds)"},
            "pillar": "Cost Optimisation"
        },
        {
            "dataset_key": "waf_co_02_01",
            "title": "CO-02-01: Auto-Termination Effectiveness",
            "type": "bar",
            "fields": {"x_field": "termination_status", "y_field": "idle_cluster_percent", "x_label": "Status", "y_label": "Idle Clusters %"},
            "pillar": "Cost Optimisation"
        }
    ]
    
    return datasets, charts

def main():
    input_file = 'dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json'
    
    print("📊 Adding WAF-Based Charts...")
    print("="*70)
    
    # Load dashboard
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Generate datasets and chart configs
    datasets, chart_configs = create_datasets_and_charts()
    
    print(f"\n✅ Generated {len(datasets)} WAF-based datasets")
    print(f"✅ Generated {len(chart_configs)} WAF-based charts")
    
    # Add datasets to dashboard
    if 'datasets' not in dashboard:
        dashboard['datasets'] = []
    
    dashboard['datasets'].extend(datasets)
    
    print(f"\n📊 Adding charts to appropriate pillar pages...")
    
    # Group charts by pillar
    charts_by_pillar = {}
    for chart in chart_configs:
        pillar = chart['pillar']
        if pillar not in charts_by_pillar:
            charts_by_pillar[pillar] = []
        charts_by_pillar[pillar].append(chart)
    
    # Add charts to each pillar page
    pages = dashboard.get('pages', [])
    
    for page in pages:
        page_name = page.get('displayName', '')
        
        if page_name in charts_by_pillar:
            pillar_charts = charts_by_pillar[page_name]
            print(f"\n   Adding {len(pillar_charts)} charts to '{page_name}' page")
            
            # Get max Y position
            max_y = 0
            for item in page['layout']:
                pos = item.get('position', {})
                y = pos.get('y', 0)
                height = pos.get('height', 0)
                max_y = max(max_y, y + height)
            
            # Add charts
            for i, chart_config in enumerate(pillar_charts):
                # Find dataset
                dataset_name = None
                for ds in datasets:
                    if chart_config['dataset_key'] in ds['displayName']:
                        dataset_name = ds['name']
                        break
                
                if not dataset_name:
                    continue
                
                # Position: 2 charts per row
                row = i // 2
                col = i % 2
                x = col * 6
                y = max_y + 1 + (row * 5)
                
                # Create widget
                widget = create_widget(
                    chart_config['type'],
                    chart_config['title'],
                    dataset_name,
                    chart_config['fields'],
                    x, y, 6, 4
                )
                
                page['layout'].append(widget)
                print(f"      • {chart_config['title']}")
    
    # Save updated dashboard
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ WAF-based charts added successfully!")
    print(f"{'='*70}")
    print(f"\nSummary:")
    print(f"   • Reliability: {len(charts_by_pillar.get('Reliability', []))} charts")
    print(f"   • Performance Efficiency: {len(charts_by_pillar.get('Performance Efficiency', []))} charts")
    print(f"   • Cost Optimisation: {len(charts_by_pillar.get('Cost Optimisation', []))} charts")
    print(f"\n🚀 Ready to redeploy!")

def create_widget(widget_type, title, dataset_name, dataset_info, x, y, width, height):
    """Create a widget with proper field mappings"""
    
    if widget_type == "line":
        widget = {
            "name": generate_id(),
            "queries": [{
                "name": f"query_{generate_id()}",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {"name": dataset_info["x_field"], "expression": f"`{dataset_info['x_field']}`"},
                        {"name": dataset_info["y_field"], "expression": f"`{dataset_info['y_field']}`"}
                    ]
                }
            }],
            "spec": {
                "version": 3,
                "widgetType": "line",
                "encodings": {
                    "x": {"fieldName": dataset_info["x_field"], "displayName": dataset_info["x_label"]},
                    "y": [{"fieldName": dataset_info["y_field"], "displayName": dataset_info["y_label"]}]
                },
                "frame": {"showTitle": True, "title": title}
            }
        }
    elif widget_type == "bar":
        widget = {
            "name": generate_id(),
            "queries": [{
                "name": f"query_{generate_id()}",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {"name": dataset_info["x_field"], "expression": f"`{dataset_info['x_field']}`"},
                        {"name": dataset_info["y_field"], "expression": f"`{dataset_info['y_field']}`"}
                    ]
                }
            }],
            "spec": {
                "version": 3,
                "widgetType": "bar",
                "encodings": {
                    "x": {"fieldName": dataset_info["x_field"], "displayName": dataset_info["x_label"]},
                    "y": [{"fieldName": dataset_info["y_field"], "displayName": dataset_info["y_label"]}]
                },
                "frame": {"showTitle": True, "title": title}
            }
        }
    else:  # pie
        widget = {
            "name": generate_id(),
            "queries": [{
                "name": f"query_{generate_id()}",
                "query": {
                    "datasetName": dataset_name,
                    "fields": [
                        {"name": dataset_info["label_field"], "expression": f"`{dataset_info['label_field']}`"},
                        {"name": dataset_info["value_field"], "expression": f"`{dataset_info['value_field']}`"}
                    ]
                }
            }],
            "spec": {
                "version": 3,
                "widgetType": "pie",
                "encodings": {
                    "label": {"fieldName": dataset_info["label_field"], "displayName": dataset_info["label_label"]},
                    "value": {"fieldName": dataset_info["value_field"], "displayName": dataset_info["value_label"]}
                },
                "frame": {"showTitle": True, "title": title}
            }
        }
    
    return {
        "widget": widget,
        "position": {"x": x, "y": y, "z": 0, "width": width, "height": height}
    }

if __name__ == "__main__":
    main()
