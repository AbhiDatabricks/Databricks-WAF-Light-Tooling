# WAF Auto App - Deployment Guide

## Overview

This app provides a **one-click deployment** that:
1. ✅ Deploys your WAF Assessment Dashboard to Databricks
2. ✅ Captures the dashboard URL automatically
3. ✅ Deploys the waf-auto app with the dashboard embedded
4. ✅ Returns a shareable app URL

## 🎯 Automated Deployment (Recommended)

### Step 1: Upload to Databricks

Choose one:
- **Option A:** Clone this repo to **Databricks Repos**
- **Option B:** Upload `waf-auto/install.ipynb` to your workspace

### Step 2: Run the Notebook

1. Open `install.ipynb` in Databricks
2. Click **Run All**
3. Wait for deployment to complete (2-5 minutes)

### Step 3: Access Your App

The notebook will display:
- 📊 **Dashboard URL** - Direct link to the dashboard
- 🚀 **App URL** - Link to the embedded dashboard app

Click the **App URL** to view your dashboard embedded in a clean interface!

## What Gets Deployed?

### 1. WAF Assessment Dashboard
- **Location:** `/Workspace/Shared/WAF-Assessment/`
- **Type:** Published Lakeview Dashboard
- **Content:** Complete WAF assessment metrics and visualizations

### 2. WAF Auto App
- **Name:** `wafauto`
- **Type:** Databricks App (FastAPI)
- **Features:**
  - Embedded dashboard in iframe
  - Clean, branded header
  - Health check endpoint (`/api/health`)
  - Config endpoint (`/api/config`)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     install.ipynb                           │
│  (Run this notebook to deploy everything automatically)     │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
               ▼                        ▼
    ┌──────────────────┐    ┌──────────────────────┐
    │   WAF Dashboard  │    │    wafauto App       │
    │   (Lakeview)     │◄───│    (FastAPI)         │
    │                  │    │  - Embeds dashboard  │
    │  - Published     │    │  - Clean UI          │
    │  - Shareable     │    │  - iframe wrapper    │
    └──────────────────┘    └──────────────────────┘
```

## Manual Deployment

If you prefer manual control:

### Deploy Dashboard First:
```python
# Use the functions from install.ipynb cells 1-6
# This will deploy and return the dashboard URL
```

### Deploy App Second:
```bash
# Via CLI
cd waf-auto
databricks bundle deploy
```

Or via **Databricks UI:**
1. Go to **Apps** → **Create app from repo**
2. Select this repository, path: `waf-auto`
3. Set environment variable: `DASHBOARD_URL=<your_dashboard_url>`
4. Click **Build** → **Run**

## Configuration

The app automatically picks up the dashboard URL during deployment, but you can override it:

### Environment Variables (in order of precedence):

1. **`DASHBOARD_URL`** - Full published dashboard URL
   ```
   DASHBOARD_URL=https://workspace.cloud.databricks.com/dashboardsv3/abc123?o=456789
   ```

2. **`DATABRICKS_HOST` + `WAF_DASHBOARD_PATH`** - Concatenated
   ```
   DATABRICKS_HOST=https://workspace.cloud.databricks.com
   WAF_DASHBOARD_PATH=dashboardsv3/abc123
   ```

3. **Default** - Falls back to demo dashboard if nothing configured

## API Endpoints

Once deployed, the app provides:

- **`GET /`** - Main page with embedded dashboard
- **`GET /api/health`** - Health check, returns `{"status":"ok"}`
- **`GET /api/config`** - Shows current dashboard URL configuration

## Troubleshooting

### Notebook fails at dashboard deployment
- Verify `dashboards/WAF_ASSESSMENTv2.1.lvdash.json` exists
- Check you have permissions to create dashboards

### Notebook fails at app deployment
- Manual deployment is provided as fallback
- Follow the manual steps shown in the notebook output
- The dashboard URL is already captured and ready to use

### App shows wrong dashboard
- Check environment variables in Apps UI
- Run `/api/config` endpoint to see what URL is configured
- Redeploy with correct `DASHBOARD_URL`

## Sharing the App

Once deployed:

1. **Get the app URL** from the notebook output
2. **Share with stakeholders** - they don't need notebook access
3. **They just click the URL** - dashboard loads in clean interface

The app URL looks like:
```
https://your-workspace.cloud.databricks.com/apps/wafauto
```

## Benefits

✅ **No manual configuration** - Dashboard URL captured automatically  
✅ **One-click deployment** - Run notebook, get app URL  
✅ **Clean interface** - Branded header, full-screen dashboard  
✅ **Easy sharing** - Send app URL to stakeholders  
✅ **No notebook access needed** - Recipients just need app access  
✅ **Always up-to-date** - Dashboard reflects latest data  

## Next Steps

After deployment:
1. Test the app URL
2. Share with your team
3. Bookmark for easy access
4. Use `/api/health` for monitoring

---

**Questions?** Check the [main README](README.md) or open an issue in the repo.

