# wafauto Databricks App

This lightweight Databricks App serves an embedded Lakeview dashboard so field teams can access the Well-Architected Framework (WAF) insights without running notebooks or manual install scripts.

## 🚀 Quick Start: Automated Deployment

**The easiest way to deploy everything:**

1. **Upload to Databricks:**
   - Clone this repo to Databricks Repos, or
   - Upload the `install.ipynb` notebook to your workspace

2. **Run `install.ipynb`:**
   - The notebook will automatically:
     - Deploy the WAF Assessment dashboard
     - Get the dashboard URL
     - Deploy the waf-auto app with the dashboard embedded
     - Return the app URL

3. **Done!** 
   - Click the app URL to access your embedded dashboard

## Structure

```
waf-auto/
├── app.yaml              # Databricks App runtime definition (name: wafauto)
├── requirements.txt      # App dependencies
├── install.ipynb         # 🆕 One-click deployment notebook
└── wafauto/
    ├── __init__.py
    └── main.py           # FastAPI server that renders the embedded dashboard
```

The FastAPI service exposes three endpoints:

- `GET /` – renders an HTML page with the published AI/BI dashboard embedded in an iframe.
- `GET /api/health` – returns `{"status":"ok"}` for app health probes.
- `GET /api/config` – returns the effective dashboard URL (taken from `DASHBOARD_URL`).

## Dashboard configuration

The app loads environment variables from any `.env` file it finds (repo root preferred). It resolves the dashboard URL in this order:

1. `DASHBOARD_URL` – embed a published Lakeview dashboard directly.
2. `DATABRICKS_HOST` + `WAF_DASHBOARD_PATH` – concatenated host/path fallback.
3. Built-in default pointing at the demo workspace dashboard.

Update `.env` to point at your workspace, or configure the variables through the Databricks Apps UI before deployment.

## Manual Deploy Steps

If you prefer to deploy manually instead of using `install.ipynb`:

### Via Databricks CLI:
```bash
cd waf-auto
databricks bundle deploy
```

### Via Databricks UI:

1. **Create the app**  
   - In the Databricks workspace UI, open **Apps** → **Create app from repo**.  
   - Select this repository and set the path to `waf-auto`.  
   - The app name is already set to `wafauto` by `app.yaml`, so Databricks will label it accordingly.

2. **Configure resources (optional for this iteration)**  
   - No Lakebase or SQL Warehouse resources are required for the embedded dashboard.  
   - Add a Database resource later if you want to persist additional metadata.

3. **Build & run**  
   - Click **Build** to install dependencies from `requirements.txt`.  
   - Click **Run** to launch the FastAPI service with Uvicorn.

4. **Open the dashboard**  
   - From the app detail page, click **Open app** to load the embedded dashboard page.  
   - Use `/api/config` or `/api/health` for diagnostics if necessary.

The app uses FastAPI + Uvicorn exclusively, so it starts quickly and only needs outbound HTTPS access to load the dashboard content.
