# Labs Proposal: WAF-AUTO (WAF Light Tooling)

**How to use this document:**  
Use this content to fill **WAF-AUTO- Labs Proposal_ Project Template.docx**. The structure matches the **Ontos** and **Zerobus** lab proposals in this folder. Copy each section below into the corresponding section of the Word template.

---

## One-sentence description (top of template)

**WAF-AUTO (Databricks WAF Light Tooling)** is a lightweight, automated assessment tool that evaluates Databricks Lakehouse implementations against the Well-Architected Framework (WAF) using System Tables, audit logs, and workspace metadata—delivering real-time scoring and actionable recommendations for governance, security, performance, and cost.

*(Optional note for template: Searching for "WAF Light Tooling" or "WAF-AUTO" in internal search should align with this project; prod.workload_insights and this codebase are the source of truth.)*

---

## Header fields (fill in template)

| Field | Value |
|-------|--------|
| **Owners** | @YOURNAME + @COMAINTAINER *(replace with actual owners)* |
| **Status** | Design sketch |
| **Product (team)** | @PMNAME (TEAM) *(e.g. Field Engineering / Solutions)* |
| **Artifact** | Dashboard + Databricks App (Streamlit) |
| **Repository name** | [GitHub repo link for Databricks-WAF-Light-Tooling] |
| **Language** | Python (Streamlit app, notebooks, scripts); SQL (dashboard queries) |
| **Target release** | YYYY-MM-DD |
| **Go link** | *(e.g. go/waf-auto or go/waf-light-tooling)* |

---

## Part 1: Request for comments

### Customer evidence

- **We're not publishing labs just for one customer.** To publish a lab project, we need at least 10 customers who want it.
- **More than 10 customers want it right now:** *(To be filled with actual customer names/evidence once gathered.)*
- **This project aims at:** Field Engineering (Solution Architects, Customer Success Engineers, Pre-sales) and Databricks customers (Data Engineers, Platform Admins, Architects). It enables consistent, automated WAF assessments instead of ad-hoc or manual evaluations.
- **Value:** Automated WAF assessments reduce time-consuming processes, inconsistencies in evaluation, and lack of automation—empowering customers to continuously optimize their Databricks environments with minimal effort. Many teams today build custom dashboards that are manually maintained, inconsistent across customers, and hard to scale; WAF Light Tooling offers a reusable, scalable, automated alternative.

**Go-To-Market (GTM) Plan**

*To date:* We have run internal presentations (e.g. Tech Summit), and Solution Architects have presented the WAF assessment tool to customers in the field. Feedback has been consistently positive—customers appreciate the automated scoring and actionable recommendations—but they have asked for more: deeper coverage of WAF controls, clearer guidance, and easier rollout across workspaces. Publishing as a Labs project will let us scale what already works and address that demand.

*After the Labs project is published,* we plan to grow usage beyond the current install base through one or more of:

- **Blog(s)** – Publish a technical blog on WAF assessment and how to use the tool.
- **Webinar(s)** – Run webinars for Field Engineering and customers on running WAF assessments.
- **Present at conference(s)** – Continue and expand presentations at internal and external events (e.g. Tech Summit, customer summits).
- **Present to partner(s)** – Brief partner SAs and enable them to use the tool in customer engagements.
- **Publish to a 3rd party registry** – If applicable.
- **Develop and deploy a Sales Play** – Standardize how SAs and CSMs offer WAF assessments in accounts.
- **Other** – Internal enablement for Field Engineering; submit to **Databricks Marketplace** and/or **https://databricks.com/learn/labs** when ready.

*In order to* scale adoption among field engineers and customers, standardize WAF assessments across engagements, and turn “customers want more” into repeatable, measurable value.

---

### Markitecture

**Sell this architecture:**

- **Dashboard:** A Lakehouse Dashboard (e.g. `WAF_ASSESSMENTv1.6`) that queries **System Tables** (`system.information_schema.tables`, `system.access.table_lineage`, `system.billing.usage`, `system.compute.clusters`, `system.query.history`, etc.) to compute WAF-aligned metrics across four pillars: **Data & AI Governance**, **Cost Optimization**, **Performance Efficiency**, and **Reliability**. Each chart is tied to WAF identifiers and Databricks Solutions with actionable recommendations.
- **Deployment path:** An **install notebook** (`install.ipynb`) deploys the dashboard into a workspace; a **Databricks App** (Streamlit, `streamlit-waf-automation/app.py`) provides a UI for multi-workspace deployment, service principal setup, and secrets management to simplify WAF assessment rollout for field engineers.
- **Integration:** The tool uses only platform-native capabilities (System Tables, Unity Catalog, Dashboards, Apps). No external SaaS; all compute and storage stay on the customer’s or internal Databricks account.
- **Why it fits the platform:** WAF assessments today are manual and inconsistent. This architecture makes WAF evaluation a first-class, repeatable workflow on the Lakehouse, driving better governance, security, performance, and cost practices and increasing value of the platform.

*Diagram:* *(Add a diagram here—e.g. Data flow: Workspace → System Tables → Dashboard + App → Scores & recommendations. Use https://mermaid.live/ or https://excalidraw.com/ as in the template.)*

---

### Graduation strategy

- **Why this is missing today:** Standardized, automated WAF assessment is not a single product offering; teams build one-off dashboards and processes. This project fills the gap with a reusable, scalable Labs asset that can later be considered for product integration or official “WAF Assessment” offering.
- **Long-term:** Keep the project healthy (http://go/labs/healthy). Goals:
  - At least one engineering/PM team could potentially take over or adopt this into the main product or official playbooks.
  - At least one Product Manager supports the idea of this project.
  - Labs guide and PM sign off on requirements and proposal.
- **After discussions with** *(Team X / Field Engineering / Solutions)*, this aligns with our WAF and customer-success story for Lakehouse adoption and optimization.

---

### Project kickoff

- Add your doc to the projects folder.
- Submit this doc to labs@databricks.com.

---

### Administrative actions

*(These are performed by your Labs guide; SLA 2 weeks.)*

- Request labs-oss@databricks.com to create a repository in https://github.com/databrickslabs for the project.
- Request labs-oss@databricks.com to enable LABS_PYPI_TOKEN if a new repository is created and PyPI is used.
- The project has a GitHub team added (https://github.com/orgs/databrickslabs/teams).
- Collaborators and teams: GitHub team has Maintain rights; owner can add more people.
- Branches: main has protection rule; PR required before merge; restrict push to main (e.g. org admins, repo admins, Maintain role).
- Tags: Tag protection rule for v*.
- Actions / General: Require PR approval for first-time contributors.

---

## Part 2: Design sketch

- **Labs reviewer and PM sign off** on requirements and proposal.
- **Submit an SDR ticket** for mandatory security and other reviews.
- **Required stakeholders sign-off** on Design sketch.

**Problem/CUJ:** Many customers and field engineers find WAF assessment time-consuming and inconsistent, which limits systematic adoption of WAF best practices. This design provides a single, automated flow: install dashboard + optional app → run queries against System Tables → get real-time scores and recommendations, reducing manual assessment effort and standardizing evaluation across engagements.

**Design in short:**  
Introduce two main components: (1) a **WAF Assessment Dashboard** (SQL + parameterized widgets) that runs on System Tables and exposes pillar-level scores and identifier-level metrics; (2) an optional **WAF Automation App** (Streamlit) for multi-workspace deployment and setup. Both use only Databricks-native APIs and System Tables; no external vendor dependencies.

*(Add a component diagram: e.g. User → App (Streamlit) / Install Notebook → Dashboard + System Tables → Scores & Recommendations.)*

---

### [Optional] Major alternatives

- **Alternative: Use OSS or commercial monitoring tools.**  
  Generic observability tools do not map to WAF pillars and identifiers or to Databricks System Tables natively. This project is purpose-built for WAF on Databricks and keeps logic and data on-platform.

- **Alternative: Buy from vendor Z.**  
  Not applicable; WAF assessment for Databricks is best delivered as a native, System Tables–driven asset that stays on the platform.

---

### [Optional] Uncertainties and dependencies

- **System Tables availability:** Queries assume standard System Tables (e.g. `system.information_schema.*`, `system.billing.usage`, `system.compute.*`, `system.query.history`) are available and permitted in the workspace.
- **Cross-workspace deployment:** The App’s multi-workspace and secrets-management flow may depend on Databricks Apps and account-level APIs; current implementation has partial AWS support with Azure/GCP planned.
- **Telemetry:** Install notebook may collect minimal, masked telemetry (e.g. first 5 chars of email, workspace ID) for adoption; can be disabled via `ENABLE_TELEMETRY = False`.

---

### Project tracking

**How do you intend to track usage via logfood telemetry?**

- **Dashboard:** Usage is attributable to workspace and SQL warehouse when the dashboard is run.
- **App:** If the project is distributed as a Databricks App, use existing app telemetry and tagging; consider http_user_agent or similar for CLI/API calls if used.
- **Notebook install:** One-time run per workspace; telemetry (if enabled) is documented in the notebook.

*(Align with template “Project Tracking” table: Library Import / Spark Config / REST API as applicable.)*

---

## Part 3: Launch checklist

*(Check off as completed; remove sections that do not apply.)*

### API Clients

*(Remove if the project is not an API client.)*  
- Unique user-agent string for telemetry if the project makes REST calls.

### Notebook Libraries

- Install path is via notebook (`install.ipynb`) and optional App; no separate “library” import in the template sense unless a Python package is added later.

### Java/Scala projects

*(Remove if not applicable.)*

### Python projects

- No conflicting project name on PyPI if publishing a package.
- Use pytest for tests where applicable; style checks (e.g. black) if code is published.
- If releasing to PyPI: correct metadata, automated release in CD, code coverage (e.g. codecov.io) for labs dash telemetry.

### Administration

- Dependabot enabled; LABS_PYPI_TOKEN if needed; Lgtm.io and CodeQL as required; GitHub URL allow-listed in Universe if needed for “Unblock my repo.”

### Enablement

- Enablement deck and/or video pitch; schedule internal enablement session for Field Engineering.

### Continuous integration

- GitHub Actions on every PR; code coverage >80% where applicable; Codecov.io integrated.

### Security & Legal

- Submit SDR ticket; fill http://go/designdoc/legal and LPP-XXX; follow up with legal-product@databricks.com.

### Longevity

- Project stays http://go/labs/healthy: code review, documented release process, release branch locked, initial release v0.0.1 or v0.1.0, end-user documentation (e.g. README, USER_GUIDE, WAF_DASHBOARD_GUIDE).

### Marketing

- Blog request (http://go/blogprocess); request to add to https://databricks.com/learn/labs if applicable.

---

## Review status (table in template)

| Reviewer (team) | LGTM blockers [?] | LGTM | Updated |
|-----------------|-------------------|------|---------|
| @Name (Labs)    |                   |      | YYYY-MM-DD |
| @Name (PM)      |                   |      | YYYY-MM-DD |
| @Name (Legal)   |                   |      | LPP-XXX |
| @Name (Security)|                   |      | SDR-XXX |

Stakeholders: Include someone representing the customer(s) of this project and SMEs for any top-level architecture or processes this project proposes changing.

---

## References in this codebase

- **README.md** – Overview, problem, solution, end users, getting started.
- **DEPLOYMENT_SUMMARY.md** – Deployed dashboard and app URLs, what they do, next steps.
- **WAF_DASHBOARD_GUIDE.md** – Metrics, SQL, and recommendations.
- **WAF_CHARTS_SUMMARY.md** – WAF identifiers and chart mapping.
- **streamlit-waf-automation/app.py** – App UI and embedding; **install.ipynb** – Dashboard deploy.
- **DONOTCHECKIN/Well-Architected Framework (WAF) - 22042025.xlsx** – WAF structure and identifiers.

Use **Labs Proposal_ Ontos.docx** and **Labs Proposal_ Zerobus - file mode.pdf** in this folder as formatting and section-order references when filling **WAF-AUTO- Labs Proposal_ Project Template.docx**.
