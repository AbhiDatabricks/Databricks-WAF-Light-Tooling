#!/usr/bin/env python3
"""
Deployment script for WAF Dashboard and Databricks App
"""
import os
import json
import requests
from datetime import datetime
import urllib3

# Disable SSL warnings for self-signed certificates
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
    print("\n" + "="*60)
    print("📊 DEPLOYING WAF ASSESSMENT DASHBOARD")
    print("="*60)
    
    # Get current user for folder path
    username = get_current_user()
    if not username:
        print("❌ Failed to get current user")
        return None
    
    parent_path = f"/Users/{username}"
    print(f"📁 Using parent path: {parent_path}")
    
    dashboard_folder = os.path.join(os.getcwd(), "dashboards")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    for fname in os.listdir(dashboard_folder):
        if fname.endswith(".lvdash.json") and not fname.startswith("Archive"):
            base_dashboard_name = fname.replace(".lvdash.json", "")
            dashboard_name = f"{base_dashboard_name}_{timestamp}"
            
            print(f"\n📄 Processing: {base_dashboard_name}")
            print(f"   ➡️  Creating as: {dashboard_name}")
            
            with open(os.path.join(dashboard_folder, fname), "r", encoding="utf-8") as f:
                dashboard_def = json.load(f)
            
            # Create dashboard
            response = requests.post(
                url=f"{API_URL}/api/2.0/lakeview/dashboards",
                headers=headers,
                json={
                    "display_name": dashboard_name,
                    "parent_path": parent_path,
                    "serialized_dashboard": json.dumps(dashboard_def),
                    "warehouse_id": None
                },
                verify=False
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                dashboard_id = result.get("dashboard_id", "")
                dashboard_path = result.get("path", "")
                print(f"✅ Created Dashboard: {dashboard_name}")
                print(f"   📊 Dashboard ID: {dashboard_id}")
                print(f"   🔗 Path: {dashboard_path}")
                print(f"   🌐 URL: {API_URL}/sql/dashboardsv3/{dashboard_id}")
                return dashboard_id
            else:
                print(f"❌ Failed to create dashboard: {response.status_code}")
                print(f"   Error: {response.text}")
                return None

def upload_app_files():
    """Upload app files to workspace"""
    print("\n📦 Uploading app files to workspace...")
    
    # Get current user for folder path
    username = get_current_user()
    if not username:
        print("❌ Failed to get current user")
        return None
    
    # Create a folder for the app in workspace
    workspace_path = f"/Users/{username}/waf-automation-app"
    
    # Upload app files
    app_files = {
        "app.py": "streamlit-waf-automation/app.py",
        "requirements.txt": "streamlit-waf-automation/requirements.txt",
        "app.yaml": "streamlit-waf-automation/app.yaml"
    }
    
    for target_name, source_path in app_files.items():
        full_source_path = os.path.join(os.getcwd(), source_path)
        with open(full_source_path, 'r') as f:
            content = f.read()
        
        # Encode content as base64
        import base64
        content_b64 = base64.b64encode(content.encode()).decode()
        
        # Upload to workspace
        workspace_file_path = f"{workspace_path}/{target_name}"
        response = requests.post(
            url=f"{API_URL}/api/2.0/workspace/import",
            headers=headers,
            json={
                "path": workspace_file_path,
                "content": content_b64,
                "language": "PYTHON" if target_name.endswith(".py") else "TEXT",
                "overwrite": True,
                "format": "SOURCE"
            },
            verify=False
        )
        
        if response.status_code in [200, 201]:
            print(f"   ✅ Uploaded: {target_name}")
        else:
            print(f"   ❌ Failed to upload {target_name}: {response.status_code}")
    
    return workspace_path

def deploy_databricks_app():
    """Deploy the Streamlit WAF Automation App"""
    print("\n" + "="*60)
    print("🚀 DEPLOYING DATABRICKS APP")
    print("="*60)
    
    # First upload the app files
    workspace_path = upload_app_files()
    if not workspace_path:
        return None
    
    app_name = "waf-automation-tool"
    
    # First, check if app already exists
    print(f"\n🔍 Checking if app '{app_name}' exists...")
    list_response = requests.get(
        url=f"{API_URL}/api/2.0/apps",
        headers=headers,
        verify=False
    )
    
    existing_app = None
    if list_response.status_code == 200:
        apps = list_response.json().get("apps", [])
        for app in apps:
            if app.get("name") == app_name:
                existing_app = app
                print(f"⚠️  App already exists with name: {app_name}")
                break
    
    # Create app configuration
    app_config = {
        "name": app_name,
        "description": "WAF Automation Tool for multi-workspace deployment",
        "resources": [
            {
                "name": "main",
                "path": workspace_path
            }
        ]
    }
    
    if existing_app:
        app_id = existing_app.get("name")
        print(f"📝 Updating existing app: {app_id}")
        
        # Update the app
        update_response = requests.patch(
            url=f"{API_URL}/api/2.0/apps/{app_id}",
            headers=headers,
            json={
                "description": app_config["description"],
                "resources": app_config.get("resources", [])
            },
            verify=False
        )
        
        if update_response.status_code in [200, 201]:
            print(f"✅ Updated App: {app_id}")
            print(f"   🌐 URL: {API_URL}/apps/{app_id}")
        else:
            print(f"⚠️  App update response: {update_response.status_code}")
            print(f"   📁 App files uploaded to: {workspace_path}")
            print(f"   🌐 URL: {API_URL}/apps/{app_id}")
    else:
        print(f"🆕 Creating new app: {app_name}")
        create_response = requests.post(
            url=f"{API_URL}/api/2.0/apps",
            headers=headers,
            json=app_config,
            verify=False
        )
        
        if create_response.status_code in [200, 201]:
            result = create_response.json()
            app_id = result.get("name", "")
            print(f"✅ Created App: {app_name}")
            print(f"   🆔 App ID: {app_id}")
            print(f"   🌐 URL: {API_URL}/apps/{app_id}")
        else:
            print(f"❌ Failed to create app: {create_response.status_code}")
            print(f"   Error: {create_response.text}")
            print(f"   📁 App files uploaded to: {workspace_path}")
            return None
    
    return app_name

def main():
    print("\n" + "🔧 WAF LIGHT TOOLING DEPLOYMENT SCRIPT" + "\n")
    print(f"🏢 Workspace: {API_URL}")
    
    # Step 1: Deploy Dashboard
    dashboard_id = deploy_dashboard()
    
    # Step 2: Deploy Databricks App
    app_id = deploy_databricks_app()
    
    print("\n" + "="*60)
    print("✅ DEPLOYMENT SUMMARY")
    print("="*60)
    if dashboard_id:
        print(f"✅ Dashboard deployed: {dashboard_id}")
    else:
        print(f"❌ Dashboard deployment failed")
    
    if app_id:
        print(f"✅ App deployed: {app_id}")
    else:
        print(f"❌ App deployment failed (this might be expected if Apps API is not available)")
    
    print("\n💡 Next Steps:")
    print("   1. Access your dashboard in the Databricks SQL workspace")
    print("   2. Configure a warehouse for the dashboard")
    print("   3. Review the WAF assessment metrics")
    print("\n")

if __name__ == "__main__":
    main()
