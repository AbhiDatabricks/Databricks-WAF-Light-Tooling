# 🔍 Databricks WAF Light Tooling

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

## 📦 Getting Started

### ⚙️ Installation

The WAF Assessment Tool can be installed in your Databricks workspace with a single notebook execution. The installation process automatically:

1. **Deploys the WAF Assessment Dashboard** - Creates a Lakeview dashboard with real-time WAF scores
2. **Publishes the Dashboard** - Configures it with a SQL warehouse for data queries
3. **Configures Embedding** - Sets up embedding domains for the Streamlit app
4. **Deploys the Streamlit App** - Creates a Databricks App with interactive WAF Guide sidebar
5. **Updates Configuration** - Automatically configures dashboard IDs and workspace settings

#### Quick Start

1. **Clone the GitHub Repository**
   ```bash
   git clone https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling.git
   ```

2. **Open in Databricks Workspace**
   - Navigate to your Databricks workspace
   - Go to **Workspace → Repos**
   - Click **Add Repo** and enter: `https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling.git`
   - Select the branch you want (default: `main`)

3. **Run `install.ipynb`**
   - Open the `install.ipynb` notebook from the repo
   - Run all cells
   - The notebook will automatically:
     - Deploy the dashboard
     - Publish with warehouse
     - Configure embedding domains
     - Upload and deploy the Streamlit app
     - Provide you with dashboard and app URLs

4. **Access Your Tools**
   - **Dashboard**: Open the dashboard URL provided in the notebook output
   - **Streamlit App**: Open the app URL provided (includes interactive WAF Guide sidebar)

#### Installation Options

- **Full Installation** (`install.ipynb`): Complete setup including dashboard and app deployment
- **App Testing** (`install_App.ipynb`): Temporary notebook for testing app deployment only (can be deleted after testing)

#### Telemetry

> **Note**: This tool collects masked email addresses (first 5 characters only) and workspace IDs for usage analytics during the initial installation only. This is a one-time telemetry collection to understand adoption. To disable telemetry, set `ENABLE_TELEMETRY = False` in the `install.ipynb` notebook.

![image](assets/waf-dashboard.png?raw=true)

### 🎯 What You Get

After installation, you'll have access to:

1. **WAF Assessment Dashboard** - Real-time scoring across 4 WAF pillars:
   - 🛡️ **Reliability** - System resilience and recovery
   - ⚖️ **Governance** - Data governance and compliance
   - 💰 **Cost Optimization** - Resource efficiency
   - ⚡ **Performance Efficiency** - Compute and query performance
   - 📊 **Summary** - Aggregated scores across all pillars

2. **Streamlit App with WAF Guide** - Interactive application featuring:
   - Embedded dashboard visualization
   - Comprehensive WAF Guide sidebar with:
     - Score calculation explanations
     - Thresholds and action items
     - Code examples for improvements
     - Best practices for each metric

---

## 📚 Documentation

### For Users

- **Installation Guide**: See [Getting Started](#-getting-started) section above
- **Dashboard Guide**: Interactive WAF Guide is available in the Streamlit app sidebar
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
├── install.ipynb              # Main installation notebook (dashboard + app)
├── install_App.ipynb           # Temporary: App deployment testing only
├── README.md                   # This file
├── DEVELOPER_DOC.md            # Developer documentation
├── LICENSE                     # MIT License
│
├── dashboards/                 # Dashboard definitions
│   ├── WAF_ASSESSMENTv1.6.lvdash.json
│   └── README.md
│
├── streamlit-waf-automation/   # Streamlit app source
│   ├── app.py                  # Main app with WAF Guide sidebar
│   ├── app.yaml                # App configuration
│   └── requirements.txt        # Python dependencies
│
├── architecture/               # Architecture diagrams and docs
│   ├── *.mmd                   # Mermaid diagram source files
│   ├── render_diagrams.html    # Browser-based diagram viewer
│   ├── README.md               # Architecture documentation
│   └── DIAGRAM_LIST.md         # Complete diagram list
│
├── assets/                     # Images and assets
│   └── waf-dashboard.png
│
└── DONOTCHECKIN/               # Development utilities (not in git)
    ├── utils/
    │   ├── scripts/            # Utility scripts
    │   └── docs/               # Planning and technical docs
    └── Integration/            # Integration examples
```

---

## 🔧 Technical Details

### Installation Process

The `install.ipynb` notebook performs the following steps:

1. **Dashboard Deployment**
   - Reads dashboard JSON from `dashboards/` folder
   - Creates Lakeview dashboard via API
   - Handles existing dashboards (updates if found)

2. **Dashboard Publishing**
   - Finds available SQL warehouse
   - Publishes dashboard with warehouse configuration
   - Verifies dashboard exists and is published

3. **Embedding Configuration**
   - Configures `*.databricksapps.com` as allowed embedding domain
   - Required for Streamlit app to embed the dashboard

4. **App Configuration**
   - Updates `app.py` with correct dashboard ID, instance URL, and workspace ID
   - Preserves comprehensive WAF Guide sidebar

5. **App Deployment**
   - Uploads app files to workspace using Workspace API
   - Deploys app using REST API (CLI not supported in notebooks)
   - Provides app URL upon successful deployment

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
- **4 Pillar Assessment**: Reliability, Governance, Cost, Performance
- **Summary View**: Aggregated scores across all pillars
- **Interactive Visualizations**: Charts and tables for each metric
- **Historical Tracking**: Monitor improvements over time

### Streamlit App Features

- **Embedded Dashboard**: Full dashboard visualization within the app
- **Interactive WAF Guide**: Comprehensive sidebar with:
  - Score calculation methodology
  - Threshold explanations
  - Actionable improvement steps
  - Code examples for each metric
- **User-Friendly Interface**: Clean, modern UI with best UX practices

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

- Ensure `*.databricksapps.com` is added to embedding domains
- Check dashboard sharing settings
- Verify app URL is correct

For more help, see the manual deployment steps provided in the installation notebook output.

---

## 🚀 Future Enhancements

Planned extensions (see `DONOTCHECKIN/utils/docs/` for details):

- **REST API Service**: Programmatic access to WAF scores
- **MCP (Model Context Protocol) Service**: Integration with AI assistants
- **WAF Recommendation Agent**: AI-powered recommendations using Databricks Vector Search and Foundation Model APIs
- **One-Click Marketplace Installation**: Package as Databricks App for easy distribution

---

## 🤝 Contributing

Want to make WAF assessments better? Contributions are welcome!  
Please fork the repo, open an issue, or submit a pull request.

**Development Setup:**
- Utility scripts and planning docs are in `DONOTCHECKIN/` (not committed to git)
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

