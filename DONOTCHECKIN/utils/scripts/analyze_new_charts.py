#!/usr/bin/env python3
"""
Analyze System Tables to Identify NEW Charts Possible
Based on actual system table data, not Excel status
"""

import json
import pandas as pd

print("📊 COMPREHENSIVE SYSTEM TABLES ANALYSIS")
print("="*70)

# Load current dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Get all queries currently used
used_tables = set()
for ds in dashboard['datasets']:
    query = ds.get('query', '')
    if 'system.' in query:
        # Extract table names
        import re
        matches = re.findall(r'system\.\w+\.\w+', query)
        used_tables.update(matches)

print(f"\n✅ Currently Using: {len(used_tables)} system tables")
for table in sorted(used_tables):
    print(f"   • {table}")

# Available system tables from docs
available_tables = {
    # Billing & Cost
    'system.billing.usage': {
        'description': 'Billable usage across account',
        'use_cases': [
            'Cost by workspace',
            'Cost by user',
            'Cost trends over time',
            'Cost by SKU/product',
            'Storage cost breakdown',
            'Compute cost breakdown'
        ]
    },
    'system.billing.list_prices': {
        'description': 'Historical SKU pricing',
        'use_cases': [
            'Price change history',
            'Cost optimization opportunities',
            'SKU price comparison'
        ]
    },
    
    # Compute & Performance
    'system.compute.clusters': {
        'description': 'Cluster configurations history',
        'use_cases': [
            'Cluster configuration changes over time',
            'Cluster lifecycle tracking',
            'Configuration drift detection'
        ]
    },
    'system.compute.node_timeline': {
        'description': 'Node utilization metrics',
        'use_cases': [
            'CPU/Memory utilization trends',
            'Node efficiency analysis',
            'Right-sizing recommendations',
            'Idle node detection'
        ]
    },
    'system.compute.warehouses': {
        'description': 'SQL warehouse configurations',
        'use_cases': [
            'Warehouse configuration history',
            'Warehouse size distribution',
            'Warehouse usage patterns'
        ]
    },
    'system.compute.warehouse_events': {
        'description': 'SQL warehouse events',
        'use_cases': [
            'Warehouse start/stop frequency',
            'Auto-scaling events',
            'Warehouse utilization patterns',
            'Idle warehouse detection'
        ]
    },
    
    # Query Performance
    'system.query.history': {
        'description': 'All queries on SQL warehouses/serverless',
        'use_cases': [
            'Query performance trends',
            'Slow query identification',
            'Query patterns analysis',
            'User query behavior',
            'Query success/failure rates',
            'Query duration distribution',
            'Most expensive queries',
            'Query concurrency patterns'
        ]
    },
    
    # Jobs & Pipelines
    'system.lakeflow.jobs': {
        'description': 'All jobs in account',
        'use_cases': [
            'Job configuration analysis',
            'Job distribution by type',
            'Job scheduling patterns'
        ]
    },
    'system.lakeflow.job_run_timeline': {
        'description': 'Job run start/end times',
        'use_cases': [
            'Job success/failure rates',
            'Job duration trends',
            'Job scheduling efficiency',
            'Failed job analysis',
            'Job run frequency',
            'Peak job execution times'
        ]
    },
    'system.lakeflow.job_task_run_timeline': {
        'description': 'Job task run details',
        'use_cases': [
            'Task-level performance',
            'Task failure analysis',
            'Task duration optimization',
            'Task dependency analysis'
        ]
    },
    'system.lakeflow.pipelines': {
        'description': 'All pipelines',
        'use_cases': [
            'Pipeline count and distribution',
            'Pipeline configuration analysis'
        ]
    },
    'system.lakeflow.pipeline_update_timeline': {
        'description': 'Pipeline update timeline',
        'use_cases': [
            'Pipeline update frequency',
            'Update success rates',
            'Update duration trends'
        ]
    },
    
    # ML & AI
    'system.mlflow.experiments_latest': {
        'description': 'MLflow experiments',
        'use_cases': [
            'Experiment count and trends',
            'Active experiments',
            'Experiment lifecycle'
        ]
    },
    'system.mlflow.runs_latest': {
        'description': 'MLflow runs',
        'use_cases': [
            'Model training runs',
            'Run success rates',
            'Training duration trends',
            'Model version tracking'
        ]
    },
    'system.mlflow.run_metrics_history': {
        'description': 'MLflow metrics timeseries',
        'use_cases': [
            'Model performance trends',
            'Metric evolution over time',
            'Model comparison'
        ]
    },
    'system.serving.served_entities': {
        'description': 'Model serving endpoints',
        'use_cases': [
            'Active model endpoints',
            'Endpoint configuration',
            'Model serving adoption'
        ]
    },
    'system.serving.endpoint_usage': {
        'description': 'Model serving usage/tokens',
        'use_cases': [
            'Model inference volume',
            'Token consumption',
            'Endpoint utilization',
            'Cost per inference',
            'Peak usage times'
        ]
    },
    
    # Data Governance
    'system.access.table_lineage': {
        'description': 'Table read/write events',
        'use_cases': [
            'Data lineage visualization',
            'Table dependency graph',
            'Most accessed tables',
            'Data flow patterns',
            'Downstream impact analysis'
        ]
    },
    'system.access.column_lineage': {
        'description': 'Column read/write events',
        'use_cases': [
            'Column-level lineage',
            'Sensitive data flow tracking',
            'Column usage patterns'
        ]
    },
    'system.data_classification.results': {
        'description': 'Sensitive data detections',
        'use_cases': [
            'Sensitive data coverage',
            'PII detection rates',
            'Classification by schema',
            'Data privacy compliance'
        ]
    },
    'system.data_quality_monitoring.table_results': {
        'description': 'Data quality monitoring',
        'use_cases': [
            'Data quality scores',
            'Quality trend analysis',
            'Failed quality checks',
            'Table freshness',
            'Completeness metrics'
        ]
    },
    
    # Security & Access
    'system.access.audit': {
        'description': 'Audit events from workspaces',
        'use_cases': [
            'User activity patterns',
            'Security event monitoring',
            'Access pattern analysis',
            'Anomaly detection',
            'Compliance reporting'
        ]
    },
    'system.access.inbound_network': {
        'description': 'Inbound network denials',
        'use_cases': [
            'Security policy violations',
            'Blocked access attempts',
            'Network security monitoring'
        ]
    },
    'system.access.outbound_network': {
        'description': 'Outbound network denials',
        'use_cases': [
            'Outbound policy violations',
            'Blocked egress attempts'
        ]
    },
    
    # Storage & Optimization
    'system.storage.predictive_optimization_operations_history': {
        'description': 'Predictive optimization',
        'use_cases': [
            'Optimization operations',
            'Storage efficiency gains',
            'Optimization success rates'
        ]
    },
    
    # Workspace Management
    'system.access.workspaces_latest': {
        'description': 'Workspace metadata',
        'use_cases': [
            'Workspace distribution',
            'Workspace configuration',
            'Multi-workspace analysis'
        ]
    },
    
    # Sharing
    'system.sharing.materialization_history': {
        'description': 'Delta Sharing materialization',
        'use_cases': [
            'Sharing activity',
            'Materialization patterns',
            'Data sharing adoption'
        ]
    },
    
    # Assistant
    'system.access.assistant_events': {
        'description': 'Databricks Assistant usage',
        'use_cases': [
            'Assistant adoption',
            'Usage patterns',
            'User engagement'
        ]
    }
}

print(f"\n\n📊 AVAILABLE SYSTEM TABLES: {len(available_tables)}")
print("="*70)

# Categorize by pillar
reliability_charts = []
performance_charts = []
cost_charts = []
governance_charts = []
security_charts = []

for table, info in available_tables.items():
    if table in used_tables:
        continue  # Skip already used
    
    # Categorize based on use cases
    use_cases = info['use_cases']
    
    # Reliability
    if any(x in table for x in ['job_run', 'pipeline', 'serving', 'mlflow']):
        reliability_charts.append((table, info))
    
    # Performance
    if any(x in table for x in ['query', 'node_timeline', 'warehouse_events']):
        performance_charts.append((table, info))
    
    # Cost
    if 'billing' in table or 'cost' in info['description'].lower():
        cost_charts.append((table, info))
    
    # Governance
    if any(x in table for x in ['lineage', 'classification', 'quality', 'workspaces']):
        governance_charts.append((table, info))
    
    # Security
    if any(x in table for x in ['audit', 'network', 'access']):
        security_charts.append((table, info))

print(f"\n🛡️ RELIABILITY - New Charts Possible ({len(reliability_charts)}):")
for table, info in reliability_charts[:10]:
    print(f"\n   📊 {table}")
    print(f"      {info['description']}")
    for use_case in info['use_cases'][:3]:
        print(f"      • {use_case}")

print(f"\n⚡ PERFORMANCE - New Charts Possible ({len(performance_charts)}):")
for table, info in performance_charts[:10]:
    print(f"\n   📊 {table}")
    print(f"      {info['description']}")
    for use_case in info['use_cases'][:3]:
        print(f"      • {use_case}")

print(f"\n💰 COST - New Charts Possible ({len(cost_charts)}):")
for table, info in cost_charts[:10]:
    print(f"\n   📊 {table}")
    print(f"      {info['description']}")
    for use_case in info['use_cases'][:3]:
        print(f"      • {use_case}")

print(f"\n🔐 GOVERNANCE - New Charts Possible ({len(governance_charts)}):")
for table, info in governance_charts[:10]:
    print(f"\n   📊 {table}")
    print(f"      {info['description']}")
    for use_case in info['use_cases'][:3]:
        print(f"      • {use_case}")

print(f"\n🔒 SECURITY - New Charts Possible ({len(security_charts)}):")
for table, info in security_charts[:10]:
    print(f"\n   📊 {table}")
    print(f"      {info['description']}")
    for use_case in info['use_cases'][:3]:
        print(f"      • {use_case}")

print(f"\n{'='*70}")
print(f"📊 SUMMARY:")
print(f"   • Reliability: {len(reliability_charts)} new chart opportunities")
print(f"   • Performance: {len(performance_charts)} new chart opportunities")
print(f"   • Cost: {len(cost_charts)} new chart opportunities")
print(f"   • Governance: {len(governance_charts)} new chart opportunities")
print(f"   • Security: {len(security_charts)} new chart opportunities")
print(f"\n💡 Total NEW charts possible: {len(reliability_charts) + len(performance_charts) + len(cost_charts) + len(governance_charts) + len(security_charts)}")
