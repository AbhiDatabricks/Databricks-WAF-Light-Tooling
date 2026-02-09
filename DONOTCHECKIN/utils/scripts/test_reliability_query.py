#!/usr/bin/env python3
"""
Test the Reliability completion percentage query
"""
import os
import json
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

print("🔍 Testing Reliability Completion Query...")
print("="*70)
print(f"🏢 Workspace: {API_URL}")
print("="*70)

# Read the query
with open('test_reliability_query.sql', 'r') as f:
    query = f.read()

# Get a SQL warehouse
print("\n📊 Finding SQL warehouse...")
warehouses_url = f"{API_URL}/api/2.0/sql/warehouses"

try:
    response = requests.get(warehouses_url, headers=headers, verify=False)
    response.raise_for_status()
    warehouses = response.json().get('warehouses', [])
    
    if not warehouses:
        print("❌ No SQL warehouses found!")
        exit(1)
    
    warehouse_id = warehouses[0]['id']
    print(f"✅ Using warehouse: {warehouses[0]['name']} (ID: {warehouse_id})")
    
    # Execute the query
    print(f"\n🚀 Executing query...")
    print("="*70)
    
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
        print("✅ Query executed successfully!")
        print("\n📊 Results:")
        print("="*70)
        
        if result.get('result') and result['result'].get('data_array'):
            # Print column names
            if result['result'].get('column_info'):
                columns = [col['name'] for col in result['result']['column_info']]
                print(f"Columns: {', '.join(columns)}")
                print("-" * 70)
            
            # Print data
            for row in result['result']['data_array']:
                print(f"  {row}")
                
            # Show completion percentage
            if len(result['result']['data_array']) > 0:
                row = result['result']['data_array'][0]
                if len(row) >= 3:
                    total = row[0] if row[0] else 0
                    implemented = row[1] if row[1] else 0
                    percent = row[2] if row[2] else 0
                    print(f"\n📈 Reliability Completion:")
                    print(f"   Total Controls: {total}")
                    print(f"   Implemented: {implemented}")
                    print(f"   Completion: {percent}%")
        else:
            print("No data returned")
    else:
        print(f"❌ Query failed with state: {state}")
        if result.get('status', {}).get('message'):
            print(f"Error: {result['status']['message']}")
        if result.get('status', {}).get('error'):
            print(f"Error details: {json.dumps(result['status']['error'], indent=2)}")
            
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response: {e.response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
