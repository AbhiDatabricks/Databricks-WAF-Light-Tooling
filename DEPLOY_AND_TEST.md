# 🚀 Quick Deploy & Test Guide

## Step 1: Deploy the API

1. **Open `deploy_api.ipynb` in your Databricks workspace**
2. **Run all cells** - The notebook will:
   - ✅ Upload all API files to workspace
   - ✅ Create startup script
   - ✅ Deploy as Databricks App
   - ✅ **Capture and display the App URL**

3. **Note the App URL** from the output (e.g., `https://waf-api-service-xxxxx.databricksapps.com`)

## Step 2: Test the API

### Option A: Using the Test Script (Recommended)

After deployment, the notebook creates a test script. Run it:

```bash
cd /Users/your-email@domain.com/waf-api
export DATABRICKS_TOKEN="your-token"
python test_api.py
```

### Option B: Quick Manual Test

Replace `<APP_URL>` with your actual app URL from Step 1:

```bash
# Health check (no auth needed)
curl https://<APP_URL>/api/v1/health

# Get all scores (requires token)
curl -H "Authorization: Bearer <YOUR_TOKEN>" https://<APP_URL>/api/v1/scores

# Get reliability scores
curl -H "Authorization: Bearer <YOUR_TOKEN>" https://<APP_URL>/api/v1/scores/reliability

# Get all metrics
curl -H "Authorization: Bearer <YOUR_TOKEN>" https://<APP_URL>/api/v1/metrics

# Get AI context
curl -H "Authorization: Bearer <YOUR_TOKEN>" https://<APP_URL>/api/v1/context
```

### Option C: Using the Quick Test Script

```bash
python DONOTCHECKIN/utils/scripts/quick_test_api.py <APP_URL> <TOKEN>
```

## Step 3: Access API Documentation

Once deployed, access interactive API docs:

- **Swagger UI**: `https://<APP_URL>/api/docs`
- **ReDoc**: `https://<APP_URL>/api/redoc`

## Expected Endpoints

The API provides these endpoints:

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/health` | GET | No | Health check |
| `/api/v1/scores` | GET | Yes | All pillar scores |
| `/api/v1/scores/{pillar}` | GET | Yes | Specific pillar (reliability, governance, cost, performance) |
| `/api/v1/metrics` | GET | Yes | All WAF control metrics |
| `/api/v1/metrics/{waf_id}` | GET | Yes | Specific metric (e.g., R-01-01) |
| `/api/v1/recommendations` | GET | Yes | WAF recommendations |
| `/api/v1/context` | GET | Yes | Structured JSON for AI agents |

## Troubleshooting

### App URL not showing?
- Check if app deployment succeeded in the notebook
- FastAPI apps may need to be deployed as Databricks Jobs instead
- See alternative deployment options in the notebook summary

### 401 Unauthorized?
- Make sure you're passing the token in the Authorization header
- Format: `Authorization: Bearer <your-token>`

### 500 Internal Server Error?
- Check if SQL Warehouse is running
- Verify `extracted_queries.json` is uploaded
- Check notebook logs for detailed error messages

### Connection refused?
- App may still be deploying (wait a minute)
- Check app status in Databricks Apps UI

## Next Steps

After successful deployment and testing:
1. ✅ API is ready for integration
2. ✅ Can be used by external applications
3. ✅ Ready for MCP service integration (Phase 3)
4. ✅ Ready for WAF Recommendation Agent (Phase 4)
