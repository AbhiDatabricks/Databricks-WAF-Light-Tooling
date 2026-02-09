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



https://github.com/user-attachments/assets/0e5a8867-6a06-4f30-ba51-38c5d09b9f57



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

