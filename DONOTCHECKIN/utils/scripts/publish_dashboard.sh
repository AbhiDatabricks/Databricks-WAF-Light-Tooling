#!/bin/bash

DASHBOARD_ID="01f102495b341fd2a36ed55be09cb1f2"
WORKSPACE_URL="https://dbc-2a8b378f-7d51.cloud.databricks.com"

echo "🔧 Publishing Dashboard with Embedding"
echo "============================================================"
echo ""
echo "Dashboard ID: $DASHBOARD_ID"
echo ""

# Get warehouse ID
echo "📦 Finding available warehouse..."
WAREHOUSE_ID=$(databricks warehouses list --output json 2>/dev/null | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$WAREHOUSE_ID" ]; then
    echo "❌ No warehouse found"
    echo ""
    echo "Please create a SQL warehouse first:"
    echo "   $WORKSPACE_URL/sql/warehouses"
    exit 1
fi

echo "✅ Using warehouse: $WAREHOUSE_ID"
echo ""

# Publish dashboard
echo "📤 Publishing dashboard..."
echo ""

# Create JSON payload
cat > /tmp/publish_payload.json << PAYLOAD
{
  "warehouse_id": "$WAREHOUSE_ID",
  "embed_credentials": true
}
PAYLOAD

# Use curl to publish (databricks CLI might not have lakeview publish yet)
echo "Manual steps to enable embedding:"
echo "============================================================"
echo ""
echo "1. Open dashboard in browser:"
echo "   $WORKSPACE_URL/sql/dashboardsv3/$DASHBOARD_ID"
echo ""
echo "2. Click the 'Share' button (top right)"
echo ""
echo "3. Click 'Embed dashboard' tab"
echo ""
echo "4. Toggle 'Enable embedding' to ON"
echo ""
echo "5. Under 'Embedding domains', add:"
echo "   *.databricksapps.com"
echo ""
echo "6. Click 'Save'"
echo ""
echo "7. Select a warehouse if prompted"
echo ""
echo "8. Refresh your app:"
echo "   https://waf-automation-tool-7474657119815190.aws.databricksapps.com"
echo ""
echo "============================================================"
echo ""

# Clean up
rm -f /tmp/publish_payload.json

