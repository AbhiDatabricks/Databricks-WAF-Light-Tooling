#!/usr/bin/env python3
"""
Script to configure Databricks workspace to allow iframe embedding from Databricks Apps
"""
import os
import json
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

# The Databricks App domain that needs to be allowed
APP_DOMAIN = "waf-automation-tool-7474657119815190.aws.databricksapps.com"

print("🔧 Configuring Databricks Workspace for iframe embedding")
print("=" * 70)

# Step 1: Get current workspace settings
print("\n📋 Step 1: Getting current workspace settings...")
response = requests.get(
    url=f"{API_URL}/api/2.0/workspace-conf",
    headers=headers,
    params={"keys": "enableWebAppIntegration"},
    verify=False
)

if response.status_code == 200:
    current_settings = response.json()
    print(f"✅ Current settings retrieved")
    print(f"   {json.dumps(current_settings, indent=2)}")
else:
    print(f"⚠️  Could not retrieve settings: {response.status_code}")
    print(f"   {response.text}")

# Step 2: Enable web app integration
print("\n📋 Step 2: Enabling web app integration...")
response = requests.patch(
    url=f"{API_URL}/api/2.0/workspace-conf",
    headers=headers,
    json={
        "enableWebAppIntegration": "true"
    },
    verify=False
)

if response.status_code == 200:
    print("✅ Web app integration enabled")
else:
    print(f"⚠️  Response: {response.status_code}")
    print(f"   {response.text}")

# Step 3: Try to configure CSP settings (if available)
print("\n📋 Step 3: Configuring Content Security Policy...")
csp_settings = {
    "enableCsp": "true",
    "cspFrameAncestors": f"'self' https://{APP_DOMAIN}"
}

response = requests.patch(
    url=f"{API_URL}/api/2.0/workspace-conf",
    headers=headers,
    json=csp_settings,
    verify=False
)

if response.status_code == 200:
    print("✅ CSP settings configured")
else:
    print(f"⚠️  CSP configuration response: {response.status_code}")
    print(f"   {response.text}")

# Step 4: Alternative - Use IP Access Lists API to ensure app can access
print("\n📋 Step 4: Checking alternative configuration options...")

# Get account ID from API URL
try:
    # Try to get workspace settings that might help
    settings_to_check = [
        "enableWebAppIntegration",
        "enableCsp", 
        "cspFrameAncestors",
        "enableIpAccessLists"
    ]
    
    response = requests.get(
        url=f"{API_URL}/api/2.0/workspace-conf",
        headers=headers,
        params={"keys": ",".join(settings_to_check)},
        verify=False
    )
    
    if response.status_code == 200:
        print("✅ Current relevant settings:")
        print(f"   {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"⚠️  Could not retrieve all settings: {e}")

print("\n" + "=" * 70)
print("📝 MANUAL STEPS REQUIRED")
print("=" * 70)
print("\nSince API-based configuration has limitations, please also:")
print("\n1. Go to Databricks Workspace Admin Console")
print("   URL: https://dbc-2a8b378f-7d51.cloud.databricks.com/settings/account")
print("\n2. Navigate to: Settings > Security > Embedding")
print("\n3. Add the following domain to 'Allowed Domains':")
print(f"   {APP_DOMAIN}")
print("\n4. Alternatively, enable 'Allow all domains' (less secure)")
print("\n5. Save the settings")
print("\n" + "=" * 70)
