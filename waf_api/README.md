# WAF Assessment Tool - REST API

REST API service providing programmatic access to WAF assessment scores and metrics.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"
export DATABRICKS_WAREHOUSE_ID="your-warehouse-id"
```

Or create a `.env` file:

```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token
DATABRICKS_WAREHOUSE_ID=your-warehouse-id
```

## Running the API

```bash
python -m waf_api.main
```

Or with uvicorn:

```bash
uvicorn waf_api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/scores` - Overall WAF scores (all pillars)
- `GET /api/v1/scores/{pillar}` - Score for specific pillar (reliability, governance, cost, performance)
- `GET /api/v1/metrics` - All WAF control metrics
- `GET /api/v1/metrics/{waf_id}` - Specific metric details (e.g., R-01-01)
- `GET /api/v1/recommendations` - Actionable recommendations
- `GET /api/v1/context` - Structured context for AI agents

## Authentication

### For External Clients

Include Databricks Personal Access Token (PAT) in Authorization header:

```
Authorization: Bearer <your-databricks-pat>
```

**How to get a PAT:**
1. Go to Databricks → User Settings → Access Tokens
2. Click "Generate New Token"
3. Copy the token and use it in API calls

**Required Token Scopes:**
- `sql` - For SQL warehouse access
- `sql.statement-execution` - For executing SQL queries

### For Databricks Apps

If calling from within a Databricks App, OAuth tokens are automatically forwarded via `X-Forwarded-Access-Token` header. No manual token needed.

### Environment Variable (Fallback)

You can also set `DATABRICKS_TOKEN` environment variable, but this is mainly for server-side use.

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
