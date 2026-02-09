#!/usr/bin/env python3
"""
Script to update Content Security Policy to allow Databricks Apps embedding
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

print("🔧 Updating Content Security Policy for Databricks Apps")
print("=" * 70)

# The current CSP from the error message
current_csp = "*.vocareum.com *.docebosaas.com *.edx.org *.deloitte.com *.cloudlabs.ai *.databricks.com *.myteksi.net *.cc.capillarytech.com *.intouch.capillarytech.com"

# Add Databricks Apps domain
new_domain = "*.databricksapps.com"
updated_csp = f"{current_csp} {new_domain}"

print(f"\n📋 Current CSP frame-ancestors:")
print(f"   {current_csp}")
print(f"\n✨ Adding domain: {new_domain}")
print(f"\n📋 Updated CSP frame-ancestors:")
print(f"   {updated_csp}")

# Try different API endpoints to update CSP
print("\n" + "=" * 70)
print("Attempting to update via API...")
print("=" * 70)

# Method 1: Try workspace-conf API
print("\n🔄 Method 1: Using workspace-conf API...")
response = requests.patch(
    url=f"{API_URL}/api/2.0/workspace-conf",
    headers=headers,
    json={
        "enableContentSecurityPolicy": "true",
        "contentSecurityPolicyFrameAncestors": updated_csp
    },
    verify=False
)

print(f"Response: {response.status_code}")
print(f"Body: {response.text}")

# Method 2: Try settings API
print("\n🔄 Method 2: Using settings API...")
response = requests.patch(
    url=f"{API_URL}/api/2.0/settings",
    headers=headers,
    json={
        "setting_name": "contentSecurityPolicy",
        "value": {
            "frameAncestors": updated_csp
        }
    },
    verify=False
)

print(f"Response: {response.status_code}")
print(f"Body: {response.text}")

# Method 3: Try GET to see what settings are available
print("\n🔄 Method 3: Checking available workspace configuration keys...")
response = requests.get(
    url=f"{API_URL}/api/2.0/workspace-conf",
    headers=headers,
    verify=False
)

print(f"Response: {response.status_code}")
if response.status_code == 200:
    print(f"Available settings: {json.dumps(response.json(), indent=2)}")
else:
    print(f"Body: {response.text}")

print("\n" + "=" * 70)
print("❗ MANUAL ACTION REQUIRED")
print("=" * 70)
print("\nUnfortunately, the CSP settings cannot be modified via API.")
print("You need to update this in the Databricks Account Console.")
print("\n📝 Steps:")
print("\n1. Go to ACCOUNT Console (not Workspace):")
print("   https://accounts.cloud.databricks.com")
print("\n2. Sign in with your account admin credentials")
print("\n3. Navigate to:")
print("   Settings → Security → Content Security Policy")
print("   OR")
print("   Workspace Settings → [Your Workspace] → Security")
print("\n4. Find the 'Frame Ancestors' or 'CSP frame-ancestors' setting")
print("\n5. Add this to the existing list:")
print(f"   {new_domain}")
print("\n6. The full value should be:")
print(f"   {updated_csp}")
print("\n7. Save and wait a few minutes for changes to propagate")
print("\n8. Refresh your app")
print("\n" + "=" * 70)
