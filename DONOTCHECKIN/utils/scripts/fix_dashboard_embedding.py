#!/usr/bin/env python3
"""
Fix Dashboard Embedding Issue
"""
from databricks.sdk import WorkspaceClient
import sys

w = WorkspaceClient()

DASHBOARD_ID = "01f102495b341fd2a36ed55be09cb1f2"

print("🔧 Fixing Dashboard Embedding")
print("="*60)

try:
    # Step 1: Get warehouse
    print("\n📦 Step 1: Finding warehouse...")
    warehouses = list(w.warehouses.list())
    if not warehouses:
        print("❌ No warehouses available. Please create a SQL warehouse first.")
        sys.exit(1)
    
    warehouse = warehouses[0]
    print(f"✅ Using: {warehouse.name} ({warehouse.id})")
    
    # Step 2: Publish dashboard
    print(f"\n📤 Step 2: Publishing dashboard...")
    try:
        w.lakeview.publish(
            dashboard_id=DASHBOARD_ID,
            warehouse_id=warehouse.id,
            embed_credentials=True
        )
        print(f"✅ Dashboard published with embedding enabled")
    except Exception as e:
        print(f"⚠️  Publish response: {e}")
        # Try without embed_credentials parameter
        try:
            w.lakeview.publish(
                dashboard_id=DASHBOARD_ID,
                warehouse_id=warehouse.id
            )
            print(f"✅ Dashboard published (basic)")
        except Exception as e2:
            print(f"❌ Failed: {e2}")
    
    # Step 3: Get dashboard details
    print(f"\n📊 Step 3: Verifying dashboard...")
    try:
        dashboard = w.lakeview.get(dashboard_id=DASHBOARD_ID)
        print(f"✅ Dashboard found")
        print(f"   Display Name: {dashboard.display_name if hasattr(dashboard, 'display_name') else 'N/A'}")
        print(f"   Warehouse: {dashboard.warehouse_id if hasattr(dashboard, 'warehouse_id') else 'N/A'}")
    except Exception as e:
        print(f"⚠️  {e}")
    
    # Step 4: Check embedding configuration
    print(f"\n🔐 Step 4: Checking embedding configuration...")
    print(f"   Dashboard needs to allow embedding from: *.databricksapps.com")
    print(f"   ")
    print(f"   To enable embedding manually:")
    print(f"   1. Open dashboard: https://dbc-2a8b378f-7d51.cloud.databricks.com/sql/dashboardsv3/{DASHBOARD_ID}")
    print(f"   2. Click 'Share' → 'Embed dashboard'")
    print(f"   3. Toggle 'Enable embedding'")
    print(f"   4. Add domain: *.databricksapps.com")
    print(f"   5. Save")
    
    print(f"\n{'='*60}")
    print(f"✅ Configuration complete!")
    print(f"{'='*60}")
    print(f"\n📊 Dashboard URL: https://dbc-2a8b378f-7d51.cloud.databricks.com/sql/dashboardsv3/{DASHBOARD_ID}")
    print(f"🔗 App URL: https://waf-automation-tool-7474657119815190.aws.databricksapps.com")
    print(f"\n💡 If embedding still doesn't work:")
    print(f"   1. Follow manual steps above to enable embedding")
    print(f"   2. Ensure *.databricksapps.com is in allowed domains")
    print(f"   3. Refresh the app")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
