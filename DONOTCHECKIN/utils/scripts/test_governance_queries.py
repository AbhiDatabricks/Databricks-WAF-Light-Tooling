#!/usr/bin/env python3
"""
Test Governance queries
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

print("🧪 Testing Governance Queries...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.5.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Get SQL warehouse
warehouses_url = f"{API_URL}/api/2.0/sql/warehouses"
response = requests.get(warehouses_url, headers=headers, verify=False)
warehouses = response.json().get('warehouses', [])
warehouse_id = warehouses[0]['id']
print(f"✅ Using warehouse: {warehouses[0]['name']} (ID: {warehouse_id})")

# Governance datasets
gov_datasets = [
    ('total_percentage_g', 'Governance - Total Percentage'),
    ('waf_principal_percentage_g', 'Governance - Principal Percentage'),
    ('waf_controls_g', 'Governance - Controls Table')
]

def find_dataset(dashboard, display_name):
    for dataset in dashboard.get('datasets', []):
        if dataset.get('displayName') == display_name:
            return dataset
    return None

def test_query(warehouse_id, query_lines, dataset_name):
    try:
        # Join like dashboard does - use ''.join() since newlines are embedded
        query = ''.join(query_lines) if isinstance(query_lines, list) else query_lines
        
        execute_url = f"{API_URL}/api/2.0/sql/statements"
        payload = {"warehouse_id": warehouse_id, "statement": query, "wait_timeout": "30s"}
        response = requests.post(execute_url, headers=headers, json=payload, verify=False)
        result = response.json()
        
        state = result.get('status', {}).get('state')
        
        if state == 'SUCCEEDED':
            if result.get('result') and result['result'].get('data_array'):
                num_rows = len(result['result']['data_array'])
                num_cols = len(result['result']['data_array'][0]) if num_rows > 0 else 0
                print(f"    ✅ Query succeeded: {num_rows} rows, {num_cols} columns")
                return True, None
            else:
                print(f"    ⚠️  Query succeeded but returned no data")
                return True, None
        else:
            error_msg = result.get('status', {}).get('message', 'Unknown error')
            print(f"    ❌ {error_msg}")
            if result.get('status', {}).get('error'):
                error_details = json.dumps(result['status']['error'], indent=2)
                print(f"    Error details: {error_details[:300]}")
            return False, error_msg
            
    except Exception as e:
        print(f"    ❌ Exception: {str(e)}")
        return False, str(e)

# Test all Governance queries
print("\n🔍 Testing Governance queries...")
print("="*70)

for display_name, description in gov_datasets:
    print(f"\n📊 Testing: {description} ({display_name})")
    
    dataset = find_dataset(dashboard, display_name)
    if not dataset:
        print(f"    ❌ Dataset not found!")
        continue
    
    query_lines = dataset.get('queryLines', [])
    if not query_lines:
        print(f"    ❌ No query found!")
        continue
    
    success, error = test_query(warehouse_id, query_lines, display_name)

print("\n" + "="*70)
print("✅ Testing complete!")
