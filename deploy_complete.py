#!/usr/bin/env python3
"""
Complete deployment script for WAF Dashboard and App with embedding configuration
"""
import os
import json
import requests
from datetime import datetime
import urllib3
import time

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

# Extract workspace ID from API URL
WORKSPACE_ID = API_URL.split("/")[2].split(".")[0].replace("dbc-", "").replace("-", "")

print("\n" + "🔧 WAF COMPLETE DEPLOYMENT SCRIPT" + "\n")
print(f"🏢 Workspace: {API_URL}")
print(f"🆔 Workspace ID: {WORKSPACE_ID}")
print("="*70)

def get_current_user():
    """Get the current user's username"""
    response = requests.get(
        url=f"{API_URL}/api/2.0/preview/scim/v2/Me",
        headers=headers,
        verify=False
    )
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("userName", "")
    return None

def deploy_dashboard():
    """Deploy the WAF Assessment Dashboard"""
    print("\n" + "="*70)
    print("📊 STEP 1: DEPLOYING DASHBOARD")
    print("="*70)
    
    username = get_current_user()
    if not username:
        print("❌ Failed to get current user")
        return None
    
    parent_path = f"/Users/{username}"
    print(f"📁 Using parent path: {parent_path}")
    
    # Get available warehouse first
    warehouse_id = get_available_warehouse()
    
    dashboard_folder = os.path.join(os.getcwd(), "dashboards")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    dashboard_id = None
    
    for fname in os.listdir(dashboard_folder):
        if fname.endswith(".lvdash.json") and "DO_NOT_DELETE" in fname:
            base_dashboard_name = fname.replace(".lvdash.json", "")
            dashboard_name = f"{base_dashboard_name}_{timestamp}"
            
            print(f"\n📄 Processing: {base_dashboard_name}")
            
            with open(os.path.join(dashboard_folder, fname), "r", encoding="utf-8") as f:
                dashboard_def = json.load(f)
            
            # Create draft dashboard with warehouse
            response = requests.post(
                url=f"{API_URL}/api/2.0/lakeview/dashboards",
                headers=headers,
                json={
                    "display_name": dashboard_name,
                    "parent_path": parent_path,
                    "serialized_dashboard": json.dumps(dashboard_def),
                    "warehouse_id": warehouse_id
                },
                verify=False
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                dashboard_id = result.get("dashboard_id", "")
                print(f"✅ Created Dashboard: {dashboard_name}")
                print(f"   📊 Dashboard ID: {dashboard_id}")
                if warehouse_id:
                    print(f"   🏭 Warehouse configured: {warehouse_id}")
                break
            else:
                print(f"❌ Failed to create dashboard: {response.status_code}")
                print(f"   Error: {response.text}")
    
    return dashboard_id

def get_available_warehouse():
    """Get the first available SQL warehouse"""
    response = requests.get(
        url=f"{API_URL}/api/2.0/sql/warehouses",
        headers=headers,
        verify=False
    )
    
    if response.status_code == 200:
        warehouses = response.json().get("warehouses", [])
        if warehouses:
            # Get first running or stopped warehouse
            for wh in warehouses:
                if wh.get("state") in ["RUNNING", "STOPPED"]:
                    warehouse_id = wh.get("id")
                    warehouse_name = wh.get("name")
                    print(f"   🏭 Found warehouse: {warehouse_name} ({warehouse_id})")
                    return warehouse_id
            # If none running/stopped, just take the first one
            warehouse_id = warehouses[0].get("id")
            warehouse_name = warehouses[0].get("name")
            print(f"   🏭 Using warehouse: {warehouse_name} ({warehouse_id})")
            return warehouse_id
    
    print("   ⚠️  No warehouses found")
    return None

def publish_dashboard(dashboard_id):
    """Publish the dashboard with an available warehouse"""
    print("\n" + "="*70)
    print("📤 STEP 2: PUBLISHING DASHBOARD WITH WAREHOUSE")
    print("="*70)
    
    if not dashboard_id:
        print("❌ No dashboard ID provided")
        return False, None
    
    # Get available warehouse
    warehouse_id = get_available_warehouse()
    
    if not warehouse_id:
        print("⚠️  No warehouse available, publishing without warehouse")
    else:
        print(f"✅ Selected warehouse ID: {warehouse_id}")
    
    # Publish the dashboard with warehouse
    response = requests.post(
        url=f"{API_URL}/api/2.0/lakeview/dashboards/{dashboard_id}/published",
        headers=headers,
        json={
            "embed_credentials": True,
            "warehouse_id": warehouse_id
        },
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Dashboard published successfully")
        return True, warehouse_id
    else:
        print(f"⚠️  Publish response: {response.status_code}")
        print(f"   {response.text}")
        return False, warehouse_id

def add_embedding_domain(dashboard_id):
    """Add *.databricksapps.com to allowed embedding domains"""
    print("\n" + "="*70)
    print("🔐 STEP 3: CONFIGURING EMBEDDING DOMAINS")
    print("="*70)
    
    if not dashboard_id:
        print("❌ No dashboard ID provided")
        return False
    
    # Try to update embedding settings
    embedding_domain = "*.databricksapps.com"
    
    # Attempt to set embedding allowed origins
    response = requests.patch(
        url=f"{API_URL}/api/2.0/lakeview/dashboards/{dashboard_id}",
        headers=headers,
        json={
            "embedding_allowed_origins": [embedding_domain]
        },
        verify=False
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Added embedding domain: {embedding_domain}")
        return True
    else:
        print(f"⚠️  Could not set via API: {response.status_code}")
        print(f"   {response.text}")
        print(f"\n📝 Manual step required:")
        print(f"   1. Open dashboard: {API_URL}/sql/dashboardsv3/{dashboard_id}")
        print(f"   2. Click 'Share' → 'Embed dashboard'")
        print(f"   3. Add domain: {embedding_domain}")
        return False

def update_app_with_embed_url(dashboard_id):
    """Update the Streamlit app with the correct embed URL"""
    print("\n" + "="*70)
    print("🔄 STEP 4: UPDATING APP WITH EMBED URL")
    print("="*70)
    
    embed_url = f"{API_URL}/embed/dashboardsv3/{dashboard_id}?o={WORKSPACE_ID}"
    
    app_code = f'''import streamlit as st

# Set page config
st.set_page_config(
    page_title="WAF Assessment Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dashboard configuration - AUTO-GENERATED BY DEPLOYMENT
INSTANCE_URL = "{API_URL}"
DASHBOARD_ID = "{dashboard_id}"
WORKSPACE_ID = "{WORKSPACE_ID}"
EMBED_URL = f"{{INSTANCE_URL}}/embed/dashboardsv3/{{DASHBOARD_ID}}?o={{WORKSPACE_ID}}"

# Title
st.title("🔍 WAF Assessment Dashboard")
st.markdown("---")

# Embed the dashboard
st.components.v1.iframe(EMBED_URL, height=800, scrolling=True)

st.markdown("---")
st.caption("💡 Databricks WAF Assessment Dashboard - Automated Well-Architected Framework Analysis")
st.caption(f"Dashboard ID: {{DASHBOARD_ID}} | Workspace: {{WORKSPACE_ID}}")
'''
    
    # Write the updated app code
    app_path = os.path.join(os.getcwd(), "streamlit-waf-automation", "app.py")
    with open(app_path, "w") as f:
        f.write(app_code)
    
    print(f"✅ Updated app.py with embed URL")
    print(f"   📍 Embed URL: {embed_url}")
    
    return True

def deploy_databricks_app():
    """Deploy the Streamlit app to Databricks Apps"""
    print("\n" + "="*70)
    print("🚀 STEP 5: DEPLOYING DATABRICKS APP")
    print("="*70)
    
    import subprocess
    
    app_name = "waf-automation-tool"
    username = get_current_user()
    workspace_path = f"/Users/{username}/waf-app-source"
    
    # Delete old files
    cmd = f'export DATABRICKS_INSECURE_TLS_SKIP_VERIFY=true && databricks workspace delete {workspace_path} --recursive'
    subprocess.run(cmd, shell=True, capture_output=True)
    
    # Upload new files
    cmd = f'export DATABRICKS_INSECURE_TLS_SKIP_VERIFY=true && databricks workspace import-dir streamlit-waf-automation {workspace_path}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
    
    if result.returncode == 0:
        print(f"✅ Uploaded app files to {workspace_path}")
    else:
        print(f"⚠️  Upload issue: {result.stderr}")
    
    # Deploy app
    print(f"\n📦 Deploying app: {app_name}")
    cmd = f'export DATABRICKS_INSECURE_TLS_SKIP_VERIFY=true && databricks apps deploy {app_name} --source-code-path /Workspace{workspace_path}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ App deployed successfully")
        # Parse deployment ID from output
        try:
            output_json = json.loads(result.stdout)
            deployment_id = output_json.get("deployment_id", "")
            print(f"   🆔 Deployment ID: {deployment_id}")
        except:
            pass
        return True
    else:
        print(f"⚠️  Deployment response: {result.stderr}")
        return False

def get_app_url():
    """Get the app URL"""
    import subprocess
    
    cmd = 'export DATABRICKS_INSECURE_TLS_SKIP_VERIFY=true && databricks apps get waf-automation-tool --output json'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            app_info = json.loads(result.stdout)
            return app_info.get("url", "")
        except:
            pass
    return None

def main():
    # Step 1: Deploy dashboard
    dashboard_id = deploy_dashboard()
    if not dashboard_id:
        print("\n❌ Deployment failed at dashboard creation")
        return
    
    # Step 2: Publish dashboard with warehouse
    time.sleep(2)  # Wait for dashboard to be ready
    published, warehouse_id = publish_dashboard(dashboard_id)
    
    # Step 3: Configure embedding
    time.sleep(2)
    add_embedding_domain(dashboard_id)
    
    # Step 4: Update app with embed URL
    update_app_with_embed_url(dashboard_id)
    
    # Step 5: Deploy app
    time.sleep(2)
    deploy_databricks_app()
    
    # Get app URL
    time.sleep(5)
    app_url = get_app_url()
    
    # Summary
    print("\n" + "="*70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("="*70)
    print(f"\n📊 Dashboard ID: {dashboard_id}")
    print(f"🔗 Dashboard URL: {API_URL}/sql/dashboardsv3/{dashboard_id}")
    print(f"📤 Published: {'Yes' if published else 'Check manually'}")
    if warehouse_id:
        print(f"🏭 Warehouse ID: {warehouse_id}")
    if app_url:
        print(f"🚀 App URL: {app_url}")
    else:
        print(f"🚀 App URL: Check via 'databricks apps get waf-automation-tool'")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Open the app URL in your browser")
    print(f"   2. The dashboard should now load with data (warehouse is configured)")
    print(f"   3. If dashboard doesn't load, manually add *.databricksapps.com to allowed domains:")
    print(f"      Dashboard → Share → Embed dashboard → Add domain")
    print(f"   4. Sign in to Databricks if prompted")
    print("\n")

if __name__ == "__main__":
    main()
