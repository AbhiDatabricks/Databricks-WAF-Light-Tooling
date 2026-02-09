# WAF Assessment Tool - Architecture & User Flow

## 📐 System Architecture Overview

```mermaid
graph TB
    subgraph "User Layer"
        U1[👤 End User]
        U2[👨‍💼 Admin/DevOps]
        U3[📊 Data Analyst]
    end
    
    subgraph "Databricks Workspace"
        subgraph "Application Layer"
            APP[🚀 Databricks App<br/>Streamlit UI<br/>WAF Guide Sidebar]
            DASH[📊 Lakeview Dashboard<br/>WAF_ASSESSMENTv1.6<br/>4 Pillars + Summary]
        end
        
        subgraph "Data Layer"
            ST1[system.information_schema.tables]
            ST2[system.billing.usage]
            ST3[system.compute.clusters]
            ST4[system.compute.warehouses]
            ST5[system.access.table_lineage]
            ST6[system.query.history]
            ST7[system.mlflow.experiments_latest]
            ST8[system.serving.served_entities]
            ST9[system.data_classification.results]
            ST10[system.access.audit]
        end
        
        subgraph "Compute Layer"
            SQLW[SQL Warehouse<br/>Serverless Starter]
            CLUSTER[Compute Clusters]
        end
        
        subgraph "Storage Layer"
            UC[Unity Catalog<br/>Metastore]
            DELTA[Delta Tables]
        end
    end
    
    subgraph "Deployment Layer"
        DEPLOY[deploy_complete.py<br/>Deployment Script]
        GIT[GitHub Repository<br/>Version Control]
    end
    
    U1 --> APP
    U2 --> APP
    U3 --> APP
    APP --> DASH
    DASH --> SQLW
    SQLW --> ST1
    SQLW --> ST2
    SQLW --> ST3
    SQLW --> ST4
    SQLW --> ST5
    SQLW --> ST6
    SQLW --> ST7
    SQLW --> ST8
    SQLW --> ST9
    SQLW --> ST10
    ST1 --> UC
    ST2 --> UC
    ST3 --> CLUSTER
    ST4 --> SQLW
    DEPLOY --> APP
    DEPLOY --> DASH
    DEPLOY --> GIT
    GIT --> DEPLOY
```

---

## 🔄 Data Flow Architecture

```mermaid
graph LR
    subgraph "Data Sources"
        SYS[System Tables<br/>13+ Tables]
    end
    
    subgraph "Data Processing"
        CTE[Shared CTEs<br/>Common Calculations]
        METRIC[Individual Metrics<br/>Percentage-Based Logic]
        THRESH[Threshold Comparison<br/>Pass/Fail Determination]
    end
    
    subgraph "Dataset Layer"
        TOTAL[total_percentage_[pillar]<br/>Overall Score<br/>1 row]
        CONTROLS[waf_controls_[pillar]<br/>Individual Metrics<br/>N rows]
        PRINCIPLE[waf_principal_percentage_[pillar]<br/>Per-Principle<br/>M rows]
        SUMMARY[total_percentage_across_pillars<br/>All Pillars<br/>4 rows]
    end
    
    subgraph "Visualization Layer"
        WIDGET1[Completion % Gauge]
        WIDGET2[Principle Breakdown Chart]
        WIDGET3[WAF Controls Table]
        WIDGET4[Summary Bar Chart]
    end
    
    SYS --> CTE
    CTE --> METRIC
    METRIC --> THRESH
    THRESH --> TOTAL
    THRESH --> CONTROLS
    THRESH --> PRINCIPLE
    TOTAL --> SUMMARY
    TOTAL --> WIDGET1
    PRINCIPLE --> WIDGET2
    CONTROLS --> WIDGET3
    SUMMARY --> WIDGET4
```

---

## 👤 User Flow - Complete Journey

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant APP as 🚀 Databricks App
    participant DASH as 📊 Dashboard
    participant SQL as SQL Warehouse
    participant ST as System Tables
    participant GUIDE as WAF Guide Sidebar
    
    U->>APP: 1. Opens App URL
    APP->>U: 2. Displays Streamlit UI
    APP->>GUIDE: 3. Loads WAF Guide Sidebar
    
    U->>GUIDE: 4. Selects Pillar (e.g., Reliability)
    GUIDE->>U: 5. Shows Pillar Overview<br/>(Score Calculation Method)
    
    U->>GUIDE: 6. Selects Metric (e.g., R-01-01)
    GUIDE->>U: 7. Shows Detailed Info:<br/>- Calculation Formula<br/>- Threshold<br/>- Actions if Low
    
    U->>DASH: 8. Views Dashboard
    DASH->>SQL: 9. Executes Queries
    SQL->>ST: 10. Queries System Tables
    ST->>SQL: 11. Returns Data
    SQL->>DASH: 12. Returns Results
    DASH->>U: 13. Displays Charts & Tables
    
    U->>DASH: 14. Sees Low Score
    U->>GUIDE: 15. Checks WAF Guide
    GUIDE->>U: 16. Shows Action Steps<br/>(SQL Examples, Best Practices)
    
    U->>U: 17. Implements Recommendations
    U->>DASH: 18. Refreshes Dashboard
    DASH->>U: 19. Sees Improved Score
```

---

## 🏗️ Detailed Component Architecture

```mermaid
graph TB
    subgraph "Frontend Components"
        subgraph "Streamlit App"
            SIDEBAR[WAF Guide Sidebar<br/>- Pillar Selection<br/>- Metric Details<br/>- Score Calculations<br/>- Action Items]
            MAIN[Main Content Area<br/>- Dashboard Embed<br/>- Iframe Container]
        end
        
        subgraph "Lakeview Dashboard"
            PAGE1[Summary Page<br/>- Overall Score<br/>- Pillar Comparison]
            PAGE2[Governance Page<br/>- 3 Widgets<br/>- Controls Table]
            PAGE3[Cost Page<br/>- 3 Widgets<br/>- Controls Table]
            PAGE4[Performance Page<br/>- 3 Widgets<br/>- Controls Table]
            PAGE5[Reliability Page<br/>- 3 Widgets<br/>- Controls Table]
        end
    end
    
    subgraph "Backend Components"
        subgraph "Dataset Queries"
            DS1[total_percentage_r<br/>Reliability Overall]
            DS2[waf_controls_r<br/>Reliability Metrics]
            DS3[waf_principal_percentage_r<br/>Reliability Principles]
            DS4[total_percentage_g<br/>Governance Overall]
            DS5[waf_controls_g<br/>Governance Metrics]
            DS6[waf_principal_percentage_g<br/>Governance Principles]
            DS7[total_percentage_c<br/>Cost Overall]
            DS8[waf_controls_c<br/>Cost Metrics]
            DS9[waf_principal_percentage_c<br/>Cost Principles]
            DS10[total_percentage_p<br/>Performance Overall]
            DS11[waf_controls_p<br/>Performance Metrics]
            DS12[waf_principal_percentage_p<br/>Performance Principles]
            DS13[total_percentage_across_pillars<br/>Summary Aggregation]
        end
        
        subgraph "Query Execution"
            SQLW[SQL Warehouse<br/>- Executes Queries<br/>- Returns Results<br/>- Caches Data]
        end
    end
    
    subgraph "Data Sources"
        ST[System Tables<br/>- 13+ Tables<br/>- Real-time Data<br/>- Historical Data]
    end
    
    SIDEBAR --> MAIN
    MAIN --> PAGE1
    MAIN --> PAGE2
    MAIN --> PAGE3
    MAIN --> PAGE4
    MAIN --> PAGE5
    
    PAGE1 --> DS13
    PAGE2 --> DS4
    PAGE2 --> DS5
    PAGE2 --> DS6
    PAGE3 --> DS7
    PAGE3 --> DS8
    PAGE3 --> DS9
    PAGE4 --> DS10
    PAGE4 --> DS11
    PAGE4 --> DS12
    PAGE5 --> DS1
    PAGE5 --> DS2
    PAGE5 --> DS3
    
    DS1 --> SQLW
    DS2 --> SQLW
    DS3 --> SQLW
    DS4 --> SQLW
    DS5 --> SQLW
    DS6 --> SQLW
    DS7 --> SQLW
    DS8 --> SQLW
    DS9 --> SQLW
    DS10 --> SQLW
    DS11 --> SQLW
    DS12 --> SQLW
    DS13 --> SQLW
    
    SQLW --> ST
```

---

## 📊 Score Calculation Flow

```mermaid
graph TD
    START[System Tables Data] --> CTE[Shared CTEs]
    
    CTE --> DELTA[delta_usage<br/>Delta Tables %]
    CTE --> DLT[dlt_usage<br/>DLT Compute %]
    CTE --> SERVERLESS[serverless_usage<br/>Serverless %]
    CTE --> PHOTON[photon_usage<br/>Photon Queries %]
    CTE --> CLUSTER[cluster_metrics<br/>Cluster Configs]
    CTE --> WAREHOUSE[warehouse_metrics<br/>Warehouse Configs]
    CTE --> TABLES[table_metrics<br/>Table Stats]
    
    DELTA --> METRIC1[R-01-01: Delta Format<br/>Score: 85.5%<br/>Threshold: 80%<br/>Status: Pass]
    DLT --> METRIC2[R-01-03: DLT Usage<br/>Score: 25.0%<br/>Threshold: 30%<br/>Status: Fail]
    SERVERLESS --> METRIC3[R-01-06: Serverless<br/>Score: 60.0%<br/>Threshold: 50%<br/>Status: Pass]
    CLUSTER --> METRIC4[R-03-01: Auto-Scale Clusters<br/>Score: 75.0%<br/>Threshold: 80%<br/>Status: Fail]
    WAREHOUSE --> METRIC5[R-03-02: Auto-Scale Warehouses<br/>Score: 90.0%<br/>Threshold: 80%<br/>Status: Pass]
    
    METRIC1 --> AGG1[Principle: Design for failure<br/>4 metrics, 2 Pass = 50%]
    METRIC2 --> AGG1
    METRIC3 --> AGG1
    
    METRIC4 --> AGG2[Principle: Autoscaling<br/>2 metrics, 1 Pass = 50%]
    METRIC5 --> AGG2
    
    AGG1 --> TOTAL[Reliability Overall<br/>8 metrics, 3 Pass = 37.5%]
    AGG2 --> TOTAL
    
    TOTAL --> DISPLAY[Dashboard Display<br/>Completion Percentage]
```

---

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV[Developer Machine<br/>- Local Code<br/>- Git Repository]
        SCRIPT[deploy_complete.py<br/>Deployment Script]
    end
    
    subgraph "Deployment Process"
        STEP1[Step 1: Deploy Dashboard<br/>- Read .lvdash.json<br/>- Create Dashboard<br/>- Get Dashboard ID]
        STEP2[Step 2: Publish Dashboard<br/>- Configure Warehouse<br/>- Enable Embedding<br/>- Verify Dashboard ID]
        STEP3[Step 3: Configure Embedding<br/>- Add *.databricksapps.com<br/>- Set Embed Credentials]
        STEP4[Step 4: Update App<br/>- Update app.py<br/>- Set Dashboard ID<br/>- Preserve WAF Guide]
        STEP5[Step 5: Deploy App<br/>- Upload to Workspace<br/>- Deploy to Apps<br/>- Activate Deployment]
    end
    
    subgraph "Databricks Workspace"
        WS_PATH[/Users/username/waf-app-source<br/>Source Code Path]
        APP_DEPLOY[Databricks App<br/>Active Deployment]
        DASH_DEPLOY[Published Dashboard<br/>With Warehouse]
    end
    
    DEV --> SCRIPT
    SCRIPT --> STEP1
    STEP1 --> STEP2
    STEP2 --> STEP3
    STEP3 --> STEP4
    STEP4 --> STEP5
    
    STEP1 --> DASH_DEPLOY
    STEP2 --> DASH_DEPLOY
    STEP3 --> DASH_DEPLOY
    STEP4 --> WS_PATH
    STEP5 --> WS_PATH
    STEP5 --> APP_DEPLOY
    
    WS_PATH --> APP_DEPLOY
```

---

## 🔐 Security & Access Flow

```mermaid
graph LR
    USER[User] --> AUTH[Databricks Authentication]
    AUTH --> PERM[Permission Check]
    
    PERM -->|Has Access| APP[App Access]
    PERM -->|No Access| DENY[Access Denied]
    
    APP --> DASH[Dashboard Access]
    DASH --> SQL[SQL Warehouse Access]
    SQL --> ST[System Tables Access]
    
    ST -->|Read Only| DATA[Data Returned]
    DATA --> DASH
    DASH --> USER
    
    subgraph "Security Layers"
        CSP[Content Security Policy<br/>frame-ancestors<br/>*.databricksapps.com]
        EMBED[Embed Credentials<br/>Embedded in Dashboard]
        UC[Unity Catalog<br/>Table Permissions]
    end
    
    APP --> CSP
    DASH --> EMBED
    ST --> UC
```

---

## 📈 Data Processing Pipeline

```mermaid
graph TB
    subgraph "Data Collection"
        COLLECT[System Tables<br/>Continuous Data Collection]
    end
    
    subgraph "Query Processing"
        Q1[Query 1: total_percentage_r<br/>Overall Reliability]
        Q2[Query 2: waf_controls_r<br/>Individual Metrics]
        Q3[Query 3: waf_principal_percentage_r<br/>Per-Principle]
        Q4[Query 4: total_percentage_g<br/>Overall Governance]
        Q5[Query 5: waf_controls_g<br/>Individual Metrics]
        Q6[Query 6: waf_principal_percentage_g<br/>Per-Principle]
        Q7[Query 7: total_percentage_c<br/>Overall Cost]
        Q8[Query 8: waf_controls_c<br/>Individual Metrics]
        Q9[Query 9: waf_principal_percentage_c<br/>Per-Principle]
        Q10[Query 10: total_percentage_p<br/>Overall Performance]
        Q11[Query 11: waf_controls_p<br/>Individual Metrics]
        Q12[Query 12: waf_principal_percentage_p<br/>Per-Principle]
        Q13[Query 13: total_percentage_across_pillars<br/>Summary]
    end
    
    subgraph "Result Aggregation"
        AGG[Combine Results<br/>Calculate Scores<br/>Apply Thresholds]
    end
    
    subgraph "Visualization"
        VIZ[Render Charts<br/>Display Tables<br/>Update UI]
    end
    
    COLLECT --> Q1
    COLLECT --> Q2
    COLLECT --> Q3
    COLLECT --> Q4
    COLLECT --> Q5
    COLLECT --> Q6
    COLLECT --> Q7
    COLLECT --> Q8
    COLLECT --> Q9
    COLLECT --> Q10
    COLLECT --> Q11
    COLLECT --> Q12
    COLLECT --> Q13
    
    Q1 --> AGG
    Q2 --> AGG
    Q3 --> AGG
    Q4 --> AGG
    Q5 --> AGG
    Q6 --> AGG
    Q7 --> AGG
    Q8 --> AGG
    Q9 --> AGG
    Q10 --> AGG
    Q11 --> AGG
    Q12 --> AGG
    Q13 --> AGG
    
    AGG --> VIZ
```

---

## 🎯 User Interaction Flow - Detailed

```mermaid
stateDiagram-v2
    [*] --> OpenApp: User opens App URL
    OpenApp --> ViewDashboard: App loads
    ViewDashboard --> CheckScore: Dashboard displays
    
    CheckScore --> HighScore: Score ≥ 80%
    CheckScore --> MediumScore: Score 60-79%
    CheckScore --> LowScore: Score < 60%
    
    HighScore --> ViewDetails: User satisfied
    MediumScore --> OpenGuide: User wants improvement
    LowScore --> OpenGuide: User needs help
    
    OpenGuide --> SelectPillar: Opens WAF Guide
    SelectPillar --> SelectMetric: Chooses pillar
    SelectMetric --> ViewCalculation: Sees metric details
    
    ViewCalculation --> ViewActions: Reviews calculation
    ViewActions --> ImplementActions: Sees action items
    ImplementActions --> ApplyChanges: Implements recommendations
    
    ApplyChanges --> RefreshDashboard: Changes applied
    RefreshDashboard --> CheckScore: Dashboard refreshed
    
    ViewDetails --> [*]: User done
    HighScore --> [*]: User done
```

---

## 📋 Dataset Relationship Architecture

```mermaid
graph TB
    subgraph "Reliability Pillar"
        R_TOTAL[total_percentage_r<br/>1 row<br/>Overall: 38%]
        R_CONTROLS[waf_controls_r<br/>8 rows<br/>Individual Metrics]
        R_PRINCIPLE[waf_principal_percentage_r<br/>3 rows<br/>Per-Principle]
    end
    
    subgraph "Governance Pillar"
        G_TOTAL[total_percentage_g<br/>1 row<br/>Overall: 65%]
        G_CONTROLS[waf_controls_g<br/>N rows<br/>Individual Metrics]
        G_PRINCIPLE[waf_principal_percentage_g<br/>M rows<br/>Per-Principle]
    end
    
    subgraph "Cost Pillar"
        C_TOTAL[total_percentage_c<br/>1 row<br/>Overall: 45%]
        C_CONTROLS[waf_controls_c<br/>9 rows<br/>Individual Metrics]
        C_PRINCIPLE[waf_principal_percentage_c<br/>3 rows<br/>Per-Principle]
    end
    
    subgraph "Performance Pillar"
        P_TOTAL[total_percentage_p<br/>1 row<br/>Overall: 72%]
        P_CONTROLS[waf_controls_p<br/>7 rows<br/>Individual Metrics]
        P_PRINCIPLE[waf_principal_percentage_p<br/>2 rows<br/>Per-Principle]
    end
    
    subgraph "Summary"
        SUMMARY[total_percentage_across_pillars<br/>4 rows<br/>All Pillars Aggregated]
    end
    
    R_TOTAL --> SUMMARY
    G_TOTAL --> SUMMARY
    C_TOTAL --> SUMMARY
    P_TOTAL --> SUMMARY
    
    R_CONTROLS -.->|Rolls up to| R_PRINCIPLE
    R_PRINCIPLE -.->|Rolls up to| R_TOTAL
    
    G_CONTROLS -.->|Rolls up to| G_PRINCIPLE
    G_PRINCIPLE -.->|Rolls up to| G_TOTAL
    
    C_CONTROLS -.->|Rolls up to| C_PRINCIPLE
    C_PRINCIPLE -.->|Rolls up to| C_TOTAL
    
    P_CONTROLS -.->|Rolls up to| P_PRINCIPLE
    P_PRINCIPLE -.->|Rolls up to| P_TOTAL
```

---

## 🔧 Component Details

### 1. **Streamlit App (app.py)**
- **Location**: `/Users/username/waf-app-source/app.py`
- **Framework**: Streamlit
- **Components**:
  - WAF Guide Sidebar (877 lines)
  - Dashboard iframe embed
  - Category/metric selection
  - Detailed explanations and action items

### 2. **Lakeview Dashboard**
- **File**: `WAF_ASSESSMENTv1.6.lvdash.json`
- **Pages**: 5 (Summary + 4 Pillars)
- **Datasets**: 13 total
- **Widgets**: ~30+ charts and tables

### 3. **System Tables Used**
- `system.information_schema.tables` - Table metadata
- `system.billing.usage` - Compute usage and costs
- `system.compute.clusters` - Cluster configurations
- `system.compute.warehouses` - Warehouse configurations
- `system.access.table_lineage` - Data lineage
- `system.query.history` - Query execution history
- `system.mlflow.experiments_latest` - ML experiments
- `system.serving.served_entities` - Model serving
- `system.data_classification.results` - Data classification
- `system.access.audit` - Access audit logs
- And more...

### 4. **Deployment Script (deploy_complete.py)**
- **Steps**:
  1. Deploy dashboard → Get dashboard ID
  2. Publish dashboard → Configure warehouse
  3. Configure embedding → Add allowed domains
  4. Update app.py → Set dashboard ID
  5. Deploy app → Upload and activate

---

## 📊 Key Metrics & Calculations

### Score Calculation Formula
```
Pillar Score = (Number of Passed Controls / Total Controls) × 100

Where:
- Passed Controls = Controls where score_percentage ≥ threshold_percentage
- Total Controls = All WAF controls in the pillar
```

### Example: Reliability Pillar
```
Total Controls: 8
Passed Controls: 3 (R-01-01, R-01-06, R-03-02)
Reliability Score = (3 / 8) × 100 = 37.5%
```

---

## 🔄 Refresh & Update Cycle

```mermaid
graph LR
    A[User Opens Dashboard] --> B[SQL Warehouse Executes Queries]
    B --> C[System Tables Return Data]
    C --> D[Queries Calculate Scores]
    D --> E[Dashboard Updates Display]
    E --> F{User Takes Action?}
    F -->|Yes| G[Implements Recommendations]
    F -->|No| H[Monitors Score]
    G --> I[System Tables Reflect Changes]
    I --> J[Next Refresh Shows Improvement]
    H --> K[Periodic Refresh]
    K --> B
    J --> B
```

---

## 🎨 UI/UX Flow

```mermaid
graph TD
    START[User Lands on App] --> SIDEBAR[WAF Guide Sidebar Visible]
    SIDEBAR --> SELECT[Select Pillar Category]
    SELECT --> OVERVIEW[See Pillar Overview<br/>Score Calculation Method]
    OVERVIEW --> METRIC[Select Specific Metric]
    METRIC --> DETAILS[View Detailed Information:<br/>- Calculation Formula<br/>- Threshold<br/>- Current Score<br/>- Actions if Low]
    
    START --> DASHBOARD[Main Dashboard View]
    DASHBOARD --> PAGES[5 Dashboard Pages]
    PAGES --> WIDGETS[Multiple Widgets per Page]
    WIDGETS --> INTERACT[User Interacts with Charts]
    
    DETAILS --> ACTIONS[User Implements Actions]
    ACTIONS --> REFRESH[Refresh Dashboard]
    REFRESH --> IMPROVED[See Improved Score]
```

---

## 📝 File Structure

```
Databricks-WAF-Light-Tooling/
├── streamlit-waf-automation/
│   ├── app.py (877 lines - WAF Guide + Dashboard Embed)
│   ├── app.yaml (App configuration)
│   └── requirements.txt (Dependencies)
├── dashboards/
│   └── WAF_ASSESSMENTv1.6.lvdash.json (11,480 lines - Dashboard definition)
├── deploy_complete.py (Deployment automation)
├── DEVELOPER_DOC.md (Dataset relationships)
├── RELIABILITY_METRICS_DOCUMENTATION.md (Reliability calculations)
└── ARCHITECTURE_DIAGRAM.md (This file)
```

---

## 🔗 Integration Points

1. **Databricks Apps Platform**
   - Hosts Streamlit application
   - Manages app lifecycle
   - Provides app URL

2. **Lakeview Dashboards**
   - Native Databricks dashboarding
   - SQL warehouse integration
   - Embedding capabilities

3. **System Tables**
   - Real-time workspace data
   - Historical usage data
   - Configuration data

4. **Unity Catalog**
   - Table metadata
   - Access control data
   - Data lineage

5. **SQL Warehouses**
   - Query execution engine
   - Data caching
   - Performance optimization

---

## 🎯 Key Design Decisions

1. **Percentage-Based Scoring**: All metrics use actual usage percentages instead of binary checks
2. **3-Dataset Pattern**: Each pillar has total, controls, and principle breakdowns
3. **Shared CTEs**: Ensures consistency across all dataset views
4. **Embedded Dashboard**: Dashboard embedded in Streamlit app for unified experience
5. **Comprehensive Guide**: WAF Guide provides detailed calculations and action items
6. **Automated Deployment**: Single script handles entire deployment process

---

**Last Updated**: February 2026  
**Version**: v1.6  
**Maintained By**: WAF Assessment Team
