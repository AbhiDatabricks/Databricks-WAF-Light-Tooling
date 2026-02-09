#!/usr/bin/env python3
"""
Test all updated datasets to ensure queries work correctly before deployment
"""
import json
import os
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read configuration from .databrickscfg
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

print("🧪 Testing All Updated Datasets...")
print("="*70)
print(f"🏢 Workspace: {API_URL}")
print("="*70)

# Read dashboard
with open('dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json', 'r') as f:
    dashboard = json.load(f)

# Get SQL warehouse ID
print("\n📋 Finding available SQL warehouse...")
warehouses_url = f"{API_URL}/api/2.0/sql/warehouses"
response = requests.get(warehouses_url, headers=headers, verify=False)
response.raise_for_status()
warehouses = response.json().get('warehouses', [])

if not warehouses:
    print("❌ No SQL warehouses found!")
    exit(1)

warehouse_id = warehouses[0]['id']
print(f"✅ Using warehouse: {warehouses[0]['name']} (ID: {warehouse_id})")

# Datasets to test
datasets_to_test = [
    # Governance
    ('total_percentage_g', 'Governance - Total Percentage'),
    ('waf_principal_percentage_g', 'Governance - Principal Percentage'),
    ('waf_controls_g', 'Governance - Controls Table'),
    
    # Cost
    ('total_percentage_c', 'Cost - Total Percentage'),
    ('waf_principal_percentage_c', 'Cost - Principal Percentage'),
    ('waf_controls_c', 'Cost - Controls Table'),
    
    # Performance
    ('total_percentage_p', 'Performance - Total Percentage'),
    ('waf_principal_percentage_p', 'Performance - Principal Percentage'),
    ('waf_controls_p', 'Performance - Controls Table'),
    
    # Reliability
    ('total_percentage_r', 'Reliability - Total Percentage'),
    ('waf_principal_percentage_r', 'Reliability - Principal Percentage'),
    ('waf_controls_r', 'Reliability - Controls Table'),
    
    # Summary
    ('total_percentage_across_pillars', 'Summary - Across Pillars')
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
        # Join query lines - preserve newlines
        query = '\n'.join(query_lines) if isinstance(query_lines, list) else query_lines
        
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
            # Print summary
            if result.get('result') and result['result'].get('data_array'):
                num_rows = len(result['result']['data_array'])
                num_cols = len(result['result']['data_array'][0]) if num_rows > 0 else 0
                
                # Show column names
                cols = []
                if result['result'].get('column_info'):
                    cols = [col['name'] for col in result['result']['column_info']]
                
                print(f"    ✅ Query succeeded: {num_rows} rows, {num_cols} columns")
                if cols:
                    print(f"       Columns: {', '.join(cols[:5])}{'...' if len(cols) > 5 else ''}")
                
                # Show first row (limited)
                if num_rows > 0:
                    first_row = result['result']['data_array'][0]
                    print(f"       First row: {str(first_row[:3])[:100]}...")
                
                return True, None
            else:
                print(f"    ⚠️  Query succeeded but returned no data")
                return True, None
        else:
            error_msg = f"Query failed: {state}"
            if result.get('status', {}).get('message'):
                error_msg += f" - {result['status']['message']}"
            print(f"    ❌ {error_msg}")
            if result.get('status', {}).get('error'):
                print(f"       Error details: {json.dumps(result['status']['error'], indent=2)[:200]}")
            return False, error_msg
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"    ❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"    ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg

# Test all datasets
print("\n🔍 Testing datasets...")
print("="*70)

results = {}
for display_name, description in datasets_to_test:
    print(f"\n📊 Testing: {description} ({display_name})")
    
    dataset = find_dataset(dashboard, display_name)
    if not dataset:
        print(f"    ❌ Dataset not found!")
        results[display_name] = {'success': False, 'error': 'Dataset not found'}
        continue
    
    query_lines = dataset.get('queryLines', [])
    if not query_lines:
        print(f"    ❌ No query found!")
        results[display_name] = {'success': False, 'error': 'No query found'}
        continue
    
    success, error = test_query(warehouse_id, query_lines, display_name)
    results[display_name] = {'success': success, 'error': error}

# Summary
print("\n" + "="*70)
print("📊 TEST SUMMARY")
print("="*70)

successful = sum(1 for r in results.values() if r['success'])
total = len(results)
failed = total - successful

print(f"\n✅ Successful: {successful}/{total}")
print(f"❌ Failed: {failed}/{total}")

if failed > 0:
    print("\n❌ Failed datasets:")
    for name, result in results.items():
        if not result['success']:
            print(f"  - {name}: {result['error']}")
    print("\n⚠️  Please fix errors before deploying!")
    exit(1)
else:
    print("\n✅ All datasets tested successfully!")
    print("🚀 Ready to deploy!")
    exit(0)
