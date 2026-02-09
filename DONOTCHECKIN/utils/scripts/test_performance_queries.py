#!/usr/bin/env python3
"""
Test Performance Efficiency queries to identify failures
"""
import json
import os
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read configuration
with open(os.path.expanduser('~/.databrickscfg'), 'r') as f:
    config = {}
    for line in f:
        line = line.strip()
        if line and not line.startswith('['):
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()

API_URL = config['host']
TOKEN = config['token']

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("🧪 Testing Performance Efficiency Queries...")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.5.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Get SQL warehouse
print("\n📋 Finding SQL warehouse...")
warehouses_url = f"{API_URL}/api/2.0/sql/warehouses"
response = requests.get(warehouses_url, headers=headers, verify=False)
response.raise_for_status()
warehouses = response.json().get('warehouses', [])

if not warehouses:
    print("❌ No SQL warehouses found!")
    exit(1)

warehouse_id = warehouses[0]['id']
print(f"✅ Using warehouse: {warehouses[0]['name']} (ID: {warehouse_id})")

# Performance Efficiency datasets
perf_datasets = [
    ('total_percentage_p', 'Performance - Total Percentage'),
    ('waf_principal_percentage_p', 'Performance - Principal Percentage'),
    ('waf_controls_p', 'Performance - Controls Table')
]

def find_dataset(dashboard, display_name):
    """Find a dataset by display name"""
    for dataset in dashboard.get('datasets', []):
        if dataset.get('displayName') == display_name:
            return dataset
    return None

def test_query(warehouse_id, query_lines, dataset_name):
    """Test a single query"""
    try:
        # Join query lines
        # Join like dashboard does - Reliability has \n embedded, so use ''.join()
        query = ''.join(query_lines) if isinstance(query_lines, list) else query_lines
        
        # Execute query
        execute_url = f"{API_URL}/api/2.0/sql/statements"
        payload = {
            "warehouse_id": warehouse_id,
            "statement": query,
            "wait_timeout": "30s"
        }
        
        response = requests.post(execute_url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
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
            error_msg = f"Query failed: {state}"
            if result.get('status', {}).get('message'):
                error_msg = result['status']['message']
            print(f"    ❌ {error_msg}")
            
            # Print full error details
            if result.get('status', {}).get('error'):
                error_details = json.dumps(result['status']['error'], indent=2)
                print(f"\n    Error details:\n{error_details}")
            
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"    ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg

# Test all Performance queries
print("\n🔍 Testing Performance Efficiency queries...")
print("="*70)

for display_name, description in perf_datasets:
    print(f"\n📊 Testing: {description} ({display_name})")
    
    dataset = find_dataset(dashboard, display_name)
    if not dataset:
        print(f"    ❌ Dataset not found!")
        continue
    
    query_lines = dataset.get('queryLines', [])
    if not query_lines:
        print(f"    ❌ No query found!")
        continue
    
    # Show first few lines of query for debugging
    query_preview = '\n'.join(query_lines[:10])
    print(f"    Query preview (first 10 lines):\n{query_preview}...")
    
    success, error = test_query(warehouse_id, query_lines, display_name)
    
    if not success:
        print(f"\n    📝 Full query (first 50 lines):")
        print('\n'.join(query_lines[:50]))

print("\n" + "="*70)
print("✅ Testing complete!")
