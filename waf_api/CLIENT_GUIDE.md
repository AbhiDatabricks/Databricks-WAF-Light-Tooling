# WAF Assessment API - Client Guide

## 🔗 API Base URL

```
https://waf-api-service-7474657119815190.aws.databricksapps.com
```

## 🔐 Authentication

The API supports **two authentication methods**:

### Method 1: Bearer Token (Recommended for External Clients)

Use your Databricks Personal Access Token (PAT) in the `Authorization` header:

```bash
Authorization: Bearer <your-databricks-pat>
```

**How to get a PAT:**
1. Go to Databricks → User Settings → Access Tokens
2. Click "Generate New Token"
3. Copy the token (you won't see it again!)
4. Use it in API calls

### Method 2: OAuth On-Behalf-Of (For Databricks Apps)

If calling from within a Databricks App, the token is automatically forwarded via `X-Forwarded-Access-Token` header. This is handled automatically by Databricks Apps.

## 📋 API Endpoints

### 1. Health Check (No Auth Required)

```bash
GET /api/v1/health
```

**Example:**
```bash
curl https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T14:30:00",
  "version": "1.0.0"
}
```

### 2. Get All Scores

```bash
GET /api/v1/scores
Authorization: Bearer <your-token>
```

**Example:**
```bash
curl -H "Authorization: Bearer dapi123..." \
  https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/scores
```

**Response:**
```json
{
  "reliability": 75.5,
  "governance": 82.3,
  "cost": 68.9,
  "performance": 71.2,
  "timestamp": "2026-02-11T14:30:00"
}
```

### 3. Get Pillar-Specific Score

```bash
GET /api/v1/scores/{pillar}
Authorization: Bearer <your-token>
```

**Pillars:** `reliability`, `governance`, `cost`, `performance`

**Example:**
```bash
curl -H "Authorization: Bearer dapi123..." \
  https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/scores/reliability
```

### 4. Get All Metrics

```bash
GET /api/v1/metrics
Authorization: Bearer <your-token>
```

**Example:**
```bash
curl -H "Authorization: Bearer dapi123..." \
  https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/metrics
```

**Response:**
```json
{
  "metrics": [
    {
      "waf_id": "R-01-01",
      "principle": "Design for failure",
      "best_practice": "Use Delta Lake for data reliability",
      "score_percentage": 85.5,
      "threshold_percentage": 80.0,
      "threshold_met": "Met",
      "implemented": "Pass"
    },
    ...
  ],
  "total_count": 52,
  "timestamp": "2026-02-11T14:30:00"
}
```

### 5. Get Specific Metric

```bash
GET /api/v1/metrics/{waf_id}
Authorization: Bearer <your-token>
```

**Example:**
```bash
curl -H "Authorization: Bearer dapi123..." \
  https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/metrics/R-01-01
```

### 6. Get Recommendations

```bash
GET /api/v1/recommendations
Authorization: Bearer <your-token>
```

### 7. Get AI Context (Structured JSON for AI Agents)

```bash
GET /api/v1/context
Authorization: Bearer <your-token>
```

**Response:**
```json
{
  "workspace_id": "2a8b378f7d51",
  "assessment_timestamp": "2026-02-11T14:30:00",
  "overall_score": 74.5,
  "pillars": {
    "reliability": {"score": 75.5, "status": "Good"},
    "governance": {"score": 82.3, "status": "Excellent"},
    "cost": {"score": 68.9, "status": "Needs Improvement"},
    "performance": {"score": 71.2, "status": "Good"}
  },
  "priority_actions": [...],
  "compliance_summary": {...}
}
```

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: `https://waf-api-service-7474657119815190.aws.databricksapps.com/api/docs`
- **ReDoc**: `https://waf-api-service-7474657119815190.aws.databricksapps.com/api/redoc`

## 💻 Code Examples

### Python

```python
import requests

API_BASE_URL = "https://waf-api-service-7474657119815190.aws.databricksapps.com"
TOKEN = "dapi123..."  # Your Databricks PAT

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Health check
response = requests.get(f"{API_BASE_URL}/api/v1/health")
print(response.json())

# Get all scores
response = requests.get(f"{API_BASE_URL}/api/v1/scores", headers=headers)
scores = response.json()
print(f"Reliability: {scores['reliability']}%")
print(f"Governance: {scores['governance']}%")

# Get specific metric
response = requests.get(f"{API_BASE_URL}/api/v1/metrics/R-01-01", headers=headers)
metric = response.json()
print(metric)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_BASE_URL = 'https://waf-api-service-7474657119815190.aws.databricksapps.com';
const TOKEN = 'dapi123...'; // Your Databricks PAT

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Health check
axios.get(`${API_BASE_URL}/api/v1/health`)
  .then(response => console.log(response.data));

// Get all scores
axios.get(`${API_BASE_URL}/api/v1/scores`, { headers })
  .then(response => {
    const scores = response.data;
    console.log(`Reliability: ${scores.reliability}%`);
    console.log(`Governance: ${scores.governance}%`);
  });
```

### cURL

```bash
# Set your token
export DATABRICKS_TOKEN="dapi123..."

# Health check (no auth)
curl https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/health

# Get scores
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/scores

# Get metrics
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/metrics
```

## 🔒 Security Best Practices

1. **Never commit tokens to code** - Use environment variables or secret management
2. **Rotate tokens regularly** - Generate new tokens periodically
3. **Use least privilege** - Only grant necessary permissions to tokens
4. **Store tokens securely** - Use secret managers (AWS Secrets Manager, Azure Key Vault, etc.)

## ⚠️ Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authorization token required"
}
```
**Solution:** Provide a valid Databricks PAT in the `Authorization` header.

### 403 Forbidden
```json
{
  "detail": "Invalid scope"
}
```
**Solution:** The token doesn't have required permissions. Ensure the token has:
- `sql` scope (for SQL warehouse access)
- `sql.statement-execution` scope (for executing queries)

### 500 Internal Server Error
```json
{
  "detail": "DATABRICKS_WAREHOUSE_ID not configured"
}
```
**Solution:** The API needs a SQL Warehouse ID configured. This is set during deployment.

## 📝 Requirements Summary

**From Client Side:**
1. ✅ **Databricks Personal Access Token (PAT)**
   - Generate from: User Settings → Access Tokens
   - Must have `sql` and `sql.statement-execution` scopes
   
2. ✅ **API Base URL**
   - `https://waf-api-service-7474657119815190.aws.databricksapps.com`
   
3. ✅ **HTTP Client**
   - Any HTTP client (curl, requests, axios, fetch, etc.)
   - Support for Bearer token authentication

4. ✅ **Network Access**
   - Must be able to reach `*.databricksapps.com` domain
   - No special firewall rules needed (standard HTTPS)

## 🎯 Quick Start

1. **Get your Databricks PAT:**
   ```
   Databricks UI → User Settings → Access Tokens → Generate New Token
   ```

2. **Test the API:**
   ```bash
   curl -H "Authorization: Bearer <your-token>" \
     https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/health
   ```

3. **Get WAF scores:**
   ```bash
   curl -H "Authorization: Bearer <your-token>" \
     https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/scores
   ```

That's it! The API is ready to use.
