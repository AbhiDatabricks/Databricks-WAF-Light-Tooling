#!/usr/bin/env python3
"""
Verify that Summary tab correctly aggregates scores from all individual pillars
"""
import json
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open(os.path.expanduser('~/.databrickscfg'), 'r') as f:
    config = {}
    for line in f:
        line = line.strip()
        if line and not line.startswith('['):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

API_URL = config['host']
TOKEN = config['token']
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

print("🔍 Verifying Summary Tab Aggregation...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.5.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Get warehouse
warehouses_url = f"{API_URL}/api/2.0/sql/warehouses"
response = requests.get(warehouses_url, headers=headers, verify=False)
warehouses = response.json().get('warehouses', [])
warehouse_id = warehouses[0]['id']

def find_dataset(dashboard, display_name):
    for dataset in dashboard.get('datasets', []):
        if dataset.get('displayName') == display_name:
            return dataset
    return None

def execute_query(warehouse_id, query_lines):
    """Execute a query and return results"""
    query = ''.join(query_lines) if isinstance(query_lines, list) else query_lines
    execute_url = f"{API_URL}/api/2.0/sql/statements"
    payload = {"warehouse_id": warehouse_id, "statement": query, "wait_timeout": "30s"}
    response = requests.post(execute_url, headers=headers, json=payload, verify=False)
    result = response.json()
    
    if result.get('status', {}).get('state') == 'SUCCEEDED':
        if result.get('result') and result['result'].get('data_array'):
            return result['result']['data_array']
    return None

# Test individual pillar queries
print("\n📊 Individual Pillar Results:")
print("="*70)

pillar_results = {}

# Governance
dataset = find_dataset(dashboard, 'total_percentage_g')
if dataset:
    results = execute_query(warehouse_id, dataset.get('queryLines', []))
    if results and len(results) > 0:
        row = results[0]
        total = row[0] if len(row) > 0 else 0
        implemented = row[1] if len(row) > 1 else 0
        percent = row[2] if len(row) > 2 else 0
        pillar_results['Data & AI Governance'] = {
            'total': total,
            'implemented': implemented,
            'percent': percent
        }
        print(f"✅ Governance: {implemented}/{total} = {percent}%")

# Cost
dataset = find_dataset(dashboard, 'total_percentage_c')
if dataset:
    results = execute_query(warehouse_id, dataset.get('queryLines', []))
    if results and len(results) > 0:
        row = results[0]
        total = row[0] if len(row) > 0 else 0
        implemented = row[1] if len(row) > 1 else 0
        percent = row[2] if len(row) > 2 else 0
        pillar_results['Cost Optimization'] = {
            'total': total,
            'implemented': implemented,
            'percent': percent
        }
        print(f"✅ Cost: {implemented}/{total} = {percent}%")

# Performance
dataset = find_dataset(dashboard, 'total_percentage_p')
if dataset:
    results = execute_query(warehouse_id, dataset.get('queryLines', []))
    if results and len(results) > 0:
        row = results[0]
        total = row[0] if len(row) > 0 else 0
        implemented = row[1] if len(row) > 1 else 0
        percent = row[2] if len(row) > 2 else 0
        pillar_results['Performance Efficiency'] = {
            'total': total,
            'implemented': implemented,
            'percent': percent
        }
        print(f"✅ Performance: {implemented}/{total} = {percent}%")

# Reliability
dataset = find_dataset(dashboard, 'total_percentage_r')
if dataset:
    results = execute_query(warehouse_id, dataset.get('queryLines', []))
    if results and len(results) > 0:
        row = results[0]
        total = row[0] if len(row) > 0 else 0
        implemented = row[1] if len(row) > 1 else 0
        percent = row[2] if len(row) > 2 else 0
        pillar_results['Reliability'] = {
            'total': total,
            'implemented': implemented,
            'percent': percent
        }
        print(f"✅ Reliability: {implemented}/{total} = {percent}%")

# Test Summary query
print("\n📊 Summary Query Results:")
print("="*70)

dataset = find_dataset(dashboard, 'total_percentage_across_pillars')
if dataset:
    results = execute_query(warehouse_id, dataset.get('queryLines', []))
    if results:
        summary_results = {}
        for row in results:
            pillar_name = row[0] if len(row) > 0 else 'Unknown'
            total = row[1] if len(row) > 1 else 0
            implemented = row[2] if len(row) > 2 else 0
            percent = row[3] if len(row) > 3 else 0
            summary_results[pillar_name] = {
                'total': total,
                'implemented': implemented,
                'percent': percent
            }
            print(f"✅ {pillar_name}: {implemented}/{total} = {percent}%")

# Compare
print("\n🔍 Comparison:")
print("="*70)

all_match = True
for pillar_name, individual in pillar_results.items():
    summary = summary_results.get(pillar_name)
    if summary:
        if (individual['total'] == summary['total'] and 
            individual['implemented'] == summary['implemented'] and
            individual['percent'] == summary['percent']):
            print(f"✅ {pillar_name}: MATCH")
        else:
            print(f"❌ {pillar_name}: MISMATCH")
            print(f"   Individual: {individual['implemented']}/{individual['total']} = {individual['percent']}%")
            print(f"   Summary:    {summary['implemented']}/{summary['total']} = {summary['percent']}%")
            all_match = False
    else:
        print(f"⚠️  {pillar_name}: Not found in summary")
        all_match = False

if all_match:
    print("\n✅ All pillars match correctly!")
else:
    print("\n❌ There are mismatches - Summary query needs to be fixed")
