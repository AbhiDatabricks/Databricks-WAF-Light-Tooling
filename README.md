# 🔍 Databricks WAF Light Tooling

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue?style=flat-square)](https://abhidatabricks.github.io/Databricks-WAF-Light-Tooling/)

> 📖 **Full documentation & live demo video:** [abhidatabricks.github.io/Databricks-WAF-Light-Tooling](https://abhidatabricks.github.io/Databricks-WAF-Light-Tooling/)

---

## 🚀 Overview

**Databricks WAF Light Tooling** is a lightweight, automated assessment tool built to evaluate Databricks Lakehouse implementations against the **Well-Architected Framework (WAF)** principles. It analyzes system tables, logs, and metadata to generate real-time scores and actionable recommendations that drive better governance, security, performance, and cost-efficiency.

---

## ❗ Problem Statement

Building a secure, efficient, and well-governed Databricks Lakehouse requires continuous adherence to WAF principles. However, the assessments generally suffer from:

- ⏱️ Time-consuming processes  
- 🔁 Inconsistencies in evaluation  
- ⚙️ Lack of automation  

---

## 🌟 Opportunity Statement

A **WAF Tool** can solve these pain points by offering:

- ✅ Automated WAF assessments  
- 📊 Real-time scoring  
- 🛠 Actionable insights  

…empowering customers to continuously optimize their Databricks environments with minimal effort.

---

## 💡 Proposed Solution

Develop a **lightweight WAF assessment tool** that:

- Automates analysis using **System Tables**, **audit logs**, and **workspace metadata**  
- Provides **real-time scoring** against WAF pillars  
- Highlights **gaps and improvement opportunities**  
- Offers **low-friction deployment** for both internal teams and customers  

---

## 🛠 Existing Alternatives

- Many teams build **custom dashboards** for monitoring.
- These are often:
  - ❌ Manually maintained  
  - ❌ Inconsistent across customers  
  - ❌ Hard to scale or reuse  

**Databricks WAF Light Tooling** offers a reusable, scalable, and automated alternative.

---

## 👥 End Users

### 1. **Databricks Field Engineering**
- Solution Architects, Customer Success Engineers, and Pre-sales teams
- Use the tool to assess customer environments and recommend WAF-aligned improvements

### 2. **Databricks Customers**
- Data Engineers, Platform Admins, and Architects
- Self-assess their environments and improve governance, security, and cost efficiency

---

## 🎬 Demo

<video width="100%" controls>
  <source src="https://abhidatabricks.github.io/Databricks-WAF-Light-Tooling/WAF2.0Demo.mp4" type="video/mp4">
</video>

---

## 📦 Getting Started

### ⚙️ Installation

The WAF Assessment Tool can be installed in your Databricks workspace with a single notebook execution. The installation process automatically:

1. **Deploys the WAF Assessment Dashboard** - Creates a Lakeview dashboard with real-time WAF scores
2. **Publishes the Dashboard** - Configures it with a SQL warehouse for data queries
3. **Configures Embedding** - Sets up embedding domains for the Databricks App
4. **Deploys the Databricks App** - The central hub with embedded dashboard, Recommendations, Progress, Reload, and Genie access
5. **Updates Configuration** - Automatically configures dashboard IDs and workspace settings

#### Permissions Required by the Installer

Before running `install.ipynb`, ensure the person running it has:

| Permission | Why |
|---|---|
| **Workspace Admin** or **Apps Admin** | Required to deploy Databricks Apps |
| **CREATE CATALOG** on the metastore | Only needed if the target catalog does not exist yet |
| **CREATE SCHEMA** on the target catalog | To create the `waf_cache` schema |
| **SELECT on `system.*`** | WAF queries read `system.billing`, `system.compute`, `system.access`, etc. |
| **An existing SQL Warehouse** | Installer attaches it to publish the dashboard |
| **Workspace files access** | To upload app source files via Workspace API |

#### Quick Start

1. **Add the Repo to Databricks**
   - Go to **Workspace → Repos → Add Repo**
   - URL: `https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling.git`
   - Branch: `main`

2. **Run `install.ipynb`**
   - Open `install.ipynb` from the repo
   - **Edit Cell 1**: set `catalog = "<your_catalog_name>"` (e.g. `"main"` or `"platform_shared"`)
   - **Run All Cells**
   - At the end you will see a full summary with ✅/❌ per step and direct links to the app, dashboard, Genie Space, and reload job

3. **Share Access** — see [Grant Access to Other Users](#-grant-access-to-other-users) below

#### Installation Options

- **Full Installation** (`install.ipynb`): Complete setup including dashboard, app, Genie Space, and reload job

**WAF Assessment App — main dashboard view:**

![WAF Assessment App Dashboard](assets/waf-app-dashboard.png?raw=true)

**WAF Recommendations (Not Met) — failing controls with actionable fixes:**

![WAF Recommendations Not Met](assets/waf-recommendations.png?raw=true)

![WAF Recommendations Detail](assets/waf-recommendations-detail.png?raw=true)

**WAF Assessment Progress — score trend over time:**

![WAF Assessment Progress](assets/waf-progress.png?raw=true)

### 🎯 What You Get

After installation, you'll have access to:

1. **WAF Assessment Dashboard** - Real-time scoring across 4 WAF pillars:
   - 🛡️ **Reliability** - System resilience and recovery
   - ⚖️ **Governance** - Data governance and compliance
   - 💰 **Cost Optimization** - Resource efficiency
   - ⚡ **Performance Efficiency** - Compute and query performance
   - 📊 **Summary** - Aggregated scores across all pillars
   - 🤖 **AI Assistant tab** - Genie Space embedded directly in the dashboard

2. **Databricks App** *(central hub)* - The single URL your team needs, featuring:
   - Embedded dashboard visualization
   - **WAF Recommendations (Not Met)** page — every failing control with score, threshold gap, and actionable fix
   - **Reload Data** button — triggers the background reload job on demand
   - **Genie** button — deep-links to the AI assistant for natural-language WAF queries
   - Comprehensive WAF Guide sidebar with score calculation explanations, thresholds, and code examples

3. **Genie Space** - AI assistant pre-loaded with all 15 WAF tables and detailed instructions:
   - Ask questions like *"Which controls are failing and what should I do?"*
   - Pre-built SQL examples for every pillar
   - Linked as an AI Assistant tab inside the dashboard

4. **WAF Reload Job** - Background Databricks Job that refreshes all WAF cache tables:
   - Triggered automatically at the end of install
   - Invokable on demand from the app's Reload button
   - Runs with full service principal permissions on `waf_cache`

---

## 📚 Documentation

📖 **[Full Documentation Site](https://abhidatabricks.github.io/Databricks-WAF-Light-Tooling/)** — includes demo video, feature overview, and getting started guide.

### For Users

- **Installation Guide**: See [Getting Started](#-getting-started) section above
- **Dashboard Guide**: Interactive WAF Guide is available in the Databricks App sidebar
- **Architecture Diagrams**: See `architecture/` folder for visual documentation

### For Developers

- **[Developer Documentation](DEVELOPER_DOC.md)**: Complete guide to dataset architecture, relationships, and data flow
- **[Architecture Diagrams](architecture/)**: 
  - System Architecture Overview
  - Data Flow Diagrams
  - User Flow - Complete Journey
  - User Interaction Flow
  - Deployment Architecture
  - And more (see `architecture/README.md` for full list)

### Architecture Documentation

The `architecture/` folder contains:
- **Mermaid diagram source files** (`.mmd`) for all architecture diagrams
- **`render_diagrams.html`** - Browser-based diagram renderer for easy viewing
- **Documentation files** explaining each diagram
- **Quick start guide** for generating diagram images

See `architecture/README.md` for details on viewing and generating diagrams.

---

## 🏗️ Project Structure

```
Databricks-WAF-Light-Tooling/
├── install.ipynb                          # Main installation notebook
├── README.md
├── LICENSE
│
├── dashboards/
│   └── WAF_ASSESSMENTv1.7.1.lvdash.json  # Lakeview dashboard template
│
├── streamlit-waf-automation/              # Databricks App source
│   ├── app.py                            # Databricks App (central hub)
│   ├── app.yaml                          # App config (catalog, job_id, warehouse_id, genie_url)
│   ├── waf_reload.py                     # Notebook: refreshes all waf_cache tables
│   ├── dashboard_queries.yaml            # All WAF SQL queries (source of truth)
│   ├── waf_controls_with_recommendations.csv  # Static recommendations catalog
│   └── requirements.txt
│
├── assets/                               # Screenshots for README
│   ├── waf-app-dashboard.png             # Main app view
│   ├── waf-recommendations.png           # Recommendations (Not Met) page
│   ├── waf-recommendations-detail.png    # Recommendations detail
│   └── waf-progress.png                 # Progress trend page
│
├── waf_core/                             # Shared Python client library
│   ├── databricks_client.py
│   ├── models.py
│   └── queries.py
│
├── waf_api/                              # FastAPI REST service (optional)
│   └── main.py
│
├── waf_agent/                            # LangChain AI agent (optional)
│   └── agent.py
│
└── waf_mcp/                              # MCP server for AI tool integration (optional)
    └── server.py
```

---

## 🔧 Technical Details

### Installation Process

The `install.ipynb` notebook performs the following steps automatically (run all cells once):

1. **Environment Checks** *(new)*
   - Validates Unity Catalog is enabled
   - Checks accessibility of `system.billing.usage`, `system.compute.clusters`, `system.access.audit`, `system.information_schema.tables`
   - Warns clearly if any are unavailable (greenfield workspaces) instead of failing silently

2. **Catalog & Schema Setup**
   - Creates the target catalog if it doesn't exist
   - Creates `waf_cache` schema

3. **WAF Recommendations Ingest** *(new)*
   - Ingests `waf_controls_with_recommendations.csv` into Delta table
   - Powers the "Recommendations (Not Met)" view in the app

4. **Genie Space Creation** *(new)*
   - Creates a Genie Space with all 15 WAF tables
   - Configures pillar-specific instructions and 6 pre-built SQL queries
   - Captures `genie_space_id` for dashboard linking

5. **Dashboard Deployment**
   - Reads the Lakeview dashboard template from `dashboards/`
   - Embeds the Genie Space via `uiSettings.overrideId` so the AI Assistant tab appears automatically
   - Creates or updates the dashboard via API

6. **Dashboard Publishing**
   - Publishes with a SQL warehouse
   - Configures `*.databricksapps.com` embedding domain

7. **App Deployment**
   - Patches `app.py` in-memory with correct `DASHBOARD_ID`, `INSTANCE_URL`, `WORKSPACE_ID`
   - Uploads all app files to workspace
   - Creates the WAF Reload Job (serverless notebook task)
   - Deploys the Databricks App and waits for it to reach RUNNING

8. **Service Principal Permissions**
   - Grants the app's SP: `USE CATALOG`, `USE SCHEMA`, `CREATE TABLE`, `MODIFY`, `SELECT` on `waf_cache`
   - Grants `USE SCHEMA + SELECT` on all relevant `system.*` schemas
   - Grants `CAN_MANAGE_RUN` on the reload job

9. **Initial Data Reload** *(new)*
   - Triggers the reload job immediately — data populates in the background (~5–10 min)

10. **Installation Summary** *(new)*
    - Per-step ✅/❌ status
    - Direct links to dashboard, app, Genie Space, reload job, and first run

### Deployment Methods

- **REST API**: Used for app deployment (CLI not supported in notebook environments)
- **Workspace API**: Used for file uploads and dashboard operations
- **Manual Fallback**: Clear instructions provided if API deployment fails

### Authentication

The installation notebook uses Databricks notebook context for authentication:
- No API keys required
- Uses `dbutils` to get API URL and token automatically
- Works seamlessly in Databricks workspace environment

---

## 🎨 Features

### Dashboard Features

- **Real-time Scoring**: Automatic calculation of WAF scores from system tables
- **4 Pillar Assessment**: Reliability, Governance, Cost Optimization, Performance Efficiency
- **Summary View**: Aggregated scores across all pillars with completion percentage bar chart
- **AI Assistant Tab**: Genie Space embedded directly in the dashboard — ask WAF questions in natural language
- **Historical Tracking**: Monitor improvements over time

### Databricks App Features

- **Embedded Dashboard**: Full Lakeview dashboard visualization within the app
- **Reload Data**: One-click button to trigger the WAF Reload background job and refresh all scores
- **View Recommendations (Not Met)**: Dedicated page listing every failing control with:
  - WAF ID, pillar, principle, best practice
  - Current score vs threshold gap
  - Full actionable recommendation text
- **View Progress**: Trend chart showing WAF score evolution across all reload runs
- **Open Dashboard in Databricks**: Direct link to the published Lakeview dashboard
- **Ask Genie**: Deep-link to the AI assistant for natural-language WAF queries
- **WAF Guide Sidebar**: Score calculation methodology, threshold explanations, and code examples for each metric

### Genie Space Features

- Pre-loaded with all 15 WAF cache tables (`waf_controls_*`, `waf_total_percentage_*`, `waf_recommendations_not_met`, etc.)
- Detailed instructions covering all 4 pillars with score band guidance (Critical / At Risk / Progressing / Mature)
- 6 pre-built SQL example queries covering the most common WAF questions
- Linked as an **AI Assistant tab** inside the Lakeview dashboard

### Installation Features

- **Greenfield Checks**: Validates Unity Catalog availability and system table accessibility at startup — warns early instead of failing silently
- **Automatic Genie Linking**: Genie Space is created before the dashboard and embedded via `uiSettings.overrideId`
- **Initial Data Reload**: Triggers the reload job automatically at the end of install — data is ready when you open the app
- **Installation Summary**: Per-step status (✅/❌) with direct links to dashboard, app, Genie Space, reload job, and first run

---

## 📊 Data Sources

The dashboard analyzes data from Databricks System Tables:

- `system.billing.usage` - Cost and usage metrics
- `system.information_schema.tables` - Table metadata
- `system.compute.clusters` - Cluster configurations
- `system.compute.warehouses` - Warehouse usage
- `system.access.audit` - Access patterns
- `system.query.history` - Query performance
- `system.mlflow.experiments_latest` - ML experiment tracking
- And more (see `DEVELOPER_DOC.md` for complete list)

---

## 👥 Grant Access to Other Users

After installation, the installer must share access with the rest of the team. Complete **all five steps** — missing any one will result in a broken experience for end-users.

### Step A — Add users to the Workspace
If users are not yet in the Databricks workspace:
- Go to **Admin Console → Users & Groups**
- Click **Add user** (individual) or **Add group** (SCIM/IdP-synced group)

### Step B — Grant access to the App

1. Go to the Databricks Apps page in your workspace
2. Find **waf-automation-tool** (or the app name shown in install output)
3. Click **Permissions**
4. Add the user/group with **CAN USE**

> The App URL is printed at the end of `install.ipynb`.

### Step C — Grant access to the Dashboard

1. Open the WAF Assessment Dashboard (URL from install output)
2. Click **Share** (top right)
3. Add the user/group
   - **CAN VIEW** — read-only access
   - **CAN EDIT** — co-author access

> The Dashboard URL is printed at the end of `install.ipynb`.

### Step D — Grant access to the Genie Space

1. Open the Genie Space (URL from install output)
2. Click **Share** (top right)
3. Add the user/group with **CAN USE**

> Without this step, users will get a permission error when clicking "Ask Genie" in the app.

### Step E — Grant read access to WAF cache tables

Run the following SQL in a SQL Editor or notebook (replace `<catalog>` and `<user_or_group>`):

```sql
-- Replace <catalog> with your WAF catalog (e.g. "main" or "useast1")
-- Replace <user_or_group> with the user email or group name exactly as in Admin Console

GRANT USE CATALOG ON CATALOG `<catalog>` TO `<user_or_group>`;
GRANT USE SCHEMA  ON SCHEMA  `<catalog>`.`waf_cache` TO `<user_or_group>`;
GRANT SELECT      ON ALL TABLES IN SCHEMA `<catalog>`.`waf_cache` TO `<user_or_group>`;
```

> This is required for the app to query WAF scores and recommendations on behalf of each user.

---

### Summary Checklist

| Step | Action | Where |
|---|---|---|
| A | Add to workspace | Admin Console → Users & Groups |
| B | App: CAN USE | Apps → waf-automation-tool → Permissions |
| C | Dashboard: CAN VIEW | Dashboard → Share |
| D | Genie Space: CAN USE | Genie Space → Share |
| E | SQL: GRANT SELECT on `waf_cache` | SQL Editor |

---

## 🔍 Troubleshooting

### Dashboard Not Loading

- Ensure the dashboard is published with a warehouse
- Check that the warehouse is running
- Verify system tables are accessible

### App Not Deploying

- Check that app files were uploaded successfully
- Verify workspace path is correct
- Try manual deployment via Databricks Apps UI (instructions provided in notebook)

### Embedding Issues

**"Embedding dashboards is not available on this domain"**

This error requires a **workspace admin** to enable embedding at the workspace level first. The per-dashboard domain allowlist will not take effect until this is done.

**Step 1 — Enable workspace-level embedding (Admin only)**

Follow the official Databricks guide:
[Control allowed embed destinations](https://docs.databricks.com/aws/en/ai-bi/admin/embed#-control-allowed-embed-destinations)

In short:
1. Go to **Admin Console → Advanced**
2. Enable **"Allow AI/BI dashboard embedding"**
3. Save

**Step 2 — Add `databricksapps.com` as an allowed destination**

Once workspace embedding is enabled, add the domain in the dashboard's Share settings:
1. Open the deployed WAF dashboard
2. Click **Share → Embed dashboard**
3. Add `*.databricksapps.com` to the allowed domains list
4. Save

The `install.ipynb` notebook attempts to configure this automatically via API, but the API call only takes effect after the workspace-level flag is turned on (Step 1 above).

For more help, see the manual deployment steps provided in the installation notebook output.

---

## 🚀 Future Enhancements

Planned extensions (see **[EXTENSION_GUIDE.md](EXTENSION_GUIDE.md)** for detailed information):

- **REST API Service**: Programmatic access to WAF scores
- **MCP (Model Context Protocol) Service**: Integration with AI assistants
- **WAF Recommendation Agent**: AI-powered recommendations using Databricks Vector Search and Foundation Model APIs
- **AI Agent Context Provider**: Structured context for external AI agents and applications
- **One-Click Marketplace Installation**: Package as Databricks App for easy distribution

> **Note**: The extension guide is marked as **Work In Progress (WIP)**. These features are planned but not yet implemented.

---

## 🤝 Contributing

Want to make WAF assessments better? Contributions are welcome!  
Please fork the repo, open an issue, or submit a pull request.

**Development Setup:**
- Main installation logic is in `install.ipynb`
- Dashboard definitions are in `dashboards/`
- App source code is in `streamlit-waf-automation/`

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📬 Contact & Support

For feature requests, support, or feedback, please use [GitHub Issues](https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling/issues).

---

## 🙏 Acknowledgments

Built with ❤️ by the Databricks Field Engineering team to help customers achieve Well-Architected Databricks Lakehouses.

---

