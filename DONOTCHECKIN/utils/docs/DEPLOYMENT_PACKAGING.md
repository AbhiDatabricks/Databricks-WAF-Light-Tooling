# 📦 WAF Assessment Tool - Databricks App Packaging & Deployment

## 🎯 Goal: One-Click Installation

**Target**: Customer clicks "Install" → Everything deploys automatically
- ✅ Dashboard
- ✅ Streamlit App with WAF Guide
- ✅ REST API
- ✅ WAF Recommendation Agent
- ✅ All dependencies configured

---

## 📋 Customer Requirements (Minimal)

### What Customer Needs

1. **Databricks Workspace** (any cloud: AWS, Azure, GCP)
   - Unity Catalog enabled (for System Tables access)
   - SQL Warehouse available (for queries)
   - **Foundation Model APIs enabled** (for agent - usually enabled by default)

2. **Permissions**:
   - Workspace admin or ability to:
     - Create dashboards
     - Deploy Databricks Apps
     - Create SQL Warehouses (or use existing)
     - Access System Tables
     - Use Foundation Model APIs (for agent)

3. **No API Keys Required!**
   - ✅ Uses Databricks built-in Anthropic endpoint (default)
   - ✅ No external API keys needed
   - ✅ Optional: Customer can override with custom endpoint if preferred

**That's it!** No infrastructure setup, no separate servers, no API keys, no complex configuration.

---

## 🏗️ Packaging as Databricks App

### App Structure

```
waf-assessment-app/
├── app/
│   ├── app.py                    # Main Streamlit app
│   ├── dashboard_embed.py        # Dashboard embedding
│   ├── waf_guide.py              # WAF Guide sidebar
│   └── agent_chat.py             # Chat interface for agent
├── api/
│   ├── main.py                   # FastAPI REST API
│   └── routes/
│       ├── scores.py
│       ├── metrics.py
│       └── chat.py               # Agent chat endpoint
├── agent/
│   ├── agent.py                  # WAF Recommendation Agent
│   ├── docs_retriever.py         # Databricks docs integration
│   └── recommendations.py
├── core/
│   ├── queries.py                # Query library
│   └── databricks_client.py
├── dashboards/
│   └── WAF_ASSESSMENTv1.6.lvdash.json
├── install/
│   ├── install.py                # Installation script
│   └── setup_agent.py            # Agent setup
├── requirements.txt
├── databricks-app.yml            # App configuration
└── README.md
```

---

## 📦 Databricks App Configuration

### `databricks-app.yml`

```yaml
name: waf-assessment-tool
version: 1.6.0
description: |
  Automated Well-Architected Framework (WAF) Assessment Tool for Databricks.
  Provides real-time scoring, recommendations, and an AI-powered assistant.

app_type: streamlit

entrypoint: app/app.py

compute:
  type: serverless
  min_workers: 1
  max_workers: 2

  environment:
    variables:
      - WAF_DASHBOARD_ID: ${DASHBOARD_ID}  # Set during install
      - DATABRICKS_WORKSPACE_URL: ${WORKSPACE_URL}
      - VECTOR_SEARCH_INDEX: ${VECTOR_INDEX_NAME}  # Vector Search index name
  
  secrets:
    # No secrets required! Uses Databricks Foundation Model APIs by default
    - name: CUSTOM_LLM_ENDPOINT
      description: "Custom LLM endpoint (optional - overrides default Databricks endpoint)"
      required: false
    - name: OPENAI_API_KEY
      description: "OpenAI API key (optional - only if customer wants to use OpenAI instead)"
      required: false

permissions:
  - dashboard:read
  - dashboard:write
  - sql:execute
  - system_tables:read

install_script: install/install.py

post_install:
  - Create dashboard
  - Configure SQL Warehouse
  - Set up agent (if API keys provided)
  - Display access URL
```

---

## 🚀 Installation Flow

### Option 1: Marketplace Installation (Simplest)

```
Customer Journey:
1. Browse Databricks Marketplace
2. Find "WAF Assessment Tool"
3. Click "Install"
4. Select workspace
5. (Optional) Enter OpenAI/Anthropic API key
6. Click "Deploy"
7. ✅ Done! App is ready
```

### Option 2: Git Repository Installation

```
Customer Journey:
1. Open Databricks Workspace
2. Go to Apps → Create App
3. Select "From Git Repository"
4. Enter: https://github.com/databricks/waf-assessment-tool
5. Click "Install"
6. (Optional) Enter API keys
7. ✅ Done!
```

### Option 3: Manual Installation (Advanced)

```
Customer Journey:
1. Clone repository
2. Run install notebook
3. Follow prompts
4. ✅ Done!
```

---

## 🔧 Installation Script (`install/install.py`)

```python
"""
WAF Assessment Tool - Installation Script
Runs automatically when app is deployed
"""
import os
import json
import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import CreateDashboardRequest

def install_waf_tool():
    """Main installation function"""
    print("🚀 Installing WAF Assessment Tool...")
    
    # 1. Get workspace client
    w = WorkspaceClient()
    workspace_url = w.config.host
    workspace_id = extract_workspace_id(workspace_url)
    
    # 2. Deploy dashboard
    print("📊 Deploying dashboard...")
    dashboard_id = deploy_dashboard(w)
    
    # 3. Configure SQL Warehouse
    print("🏭 Configuring SQL Warehouse...")
    warehouse_id = get_or_create_warehouse(w)
    
    # 4. Publish dashboard
    print("📤 Publishing dashboard...")
    publish_dashboard(w, dashboard_id, warehouse_id)
    
    # 5. Set up agent (if API keys provided)
    print("🤖 Setting up WAF Recommendation Agent...")
    agent_configured = setup_agent()
    
    # 6. Update app environment variables
    print("⚙️  Configuring app...")
    update_app_config(dashboard_id, workspace_id)
    
    # 7. Display success message
    print("\n✅ Installation Complete!")
    print(f"📊 Dashboard: {workspace_url}/sql/dashboardsv3/{dashboard_id}")
    print(f"🚀 App: {workspace_url}/apps/...")
    print("🤖 Agent: Ready (using Databricks Foundation Model)")
    
    return {
        "dashboard_id": dashboard_id,
        "warehouse_id": warehouse_id,
        "agent_configured": agent_configured
    }

def deploy_dashboard(w: WorkspaceClient) -> str:
    """Deploy WAF Assessment Dashboard"""
    dashboard_path = "dashboards/WAF_ASSESSMENTv1.6.lvdash.json"
    
    with open(dashboard_path, 'r') as f:
        dashboard_def = json.load(f)
    
    # Get current user
    user = w.current_user.me()
    parent_path = f"/Users/{user.user_name}"
    
    # Create dashboard
    dashboard = w.lakeview.dashboards.create(
        display_name="WAF Assessment Dashboard",
        parent_path=parent_path,
        serialized_dashboard=json.dumps(dashboard_def)
    )
    
    return dashboard.dashboard_id

def setup_agent() -> bool:
    """Set up WAF Recommendation Agent - Uses Databricks Foundation Model by default"""
    # Agent always available - uses Databricks Foundation Model APIs
    # No API keys required!
    print("   ✅ Agent configured (using Databricks Foundation Model - Anthropic Claude)")
    return True

def update_app_config(dashboard_id: str, workspace_id: str):
    """Update app environment variables"""
    # Set environment variables for app
    os.environ["WAF_DASHBOARD_ID"] = dashboard_id
    os.environ["DATABRICKS_WORKSPACE_ID"] = workspace_id
    os.environ["DATABRICKS_WORKSPACE_URL"] = w.config.host
```

---

## 📱 App Entry Point (`app/app.py`)

```python
"""
WAF Assessment Tool - Main Streamlit App
"""
import streamlit as st
import os
from dashboard_embed import embed_dashboard
from waf_guide import render_waf_guide
from agent_chat import render_chat_interface

# Configuration
DASHBOARD_ID = os.getenv("WAF_DASHBOARD_ID")
WORKSPACE_URL = os.getenv("DATABRICKS_WORKSPACE_URL")
WORKSPACE_ID = os.getenv("DATABRICKS_WORKSPACE_ID")

# Agent is always enabled - uses Databricks Foundation Model by default
# No API keys required!
AGENT_ENABLED = True

st.set_page_config(
    page_title="WAF Assessment Tool",
    page_icon="🔍",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.title("🔍 WAF Assessment Tool")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📖 WAF Guide", "🤖 Ask Agent"] if AGENT_ENABLED else ["📊 Dashboard", "📖 WAF Guide"]
    )

# Main content
if page == "📊 Dashboard":
    embed_dashboard(DASHBOARD_ID, WORKSPACE_URL, WORKSPACE_ID)
    
elif page == "📖 WAF Guide":
    render_waf_guide()
    
elif page == "🤖 Ask Agent" and AGENT_ENABLED:
    render_chat_interface()
    
# Agent is always available - uses Databricks Foundation Model
# No configuration needed!
```

---

## 🤖 Agent Setup (`install/setup_agent.py`)

```python
"""
Set up WAF Recommendation Agent
"""
import os
from agent.agent import WAFRecommendationAgent
from agent.docs_retriever import DatabricksDocsRetriever

def setup_agent():
    """Initialize agent with configuration - Uses Databricks Foundation Model by default"""
    from databricks.sdk import WorkspaceClient
    
    w = WorkspaceClient()
    
    # Set up Vector Search index for docs
    print("   📚 Setting up Vector Search index...")
    index_name = setup_vector_search_index()
    
    # Initialize docs retriever (uses Databricks Vector Search)
    print("   📖 Initializing docs retriever...")
    docs_retriever = DatabricksDocsRetriever(index_name=index_name)
    
    # Check for custom endpoint (optional override)
    custom_endpoint = os.getenv("CUSTOM_LLM_ENDPOINT")
    openai_key = os.getenv("OPENAI_API_KEY")  # Optional: customer override
    
    # Initialize agent
    print("   🤖 Initializing agent...")
    
    if custom_endpoint:
        # Use custom endpoint if provided
        agent = WAFRecommendationAgent(
            llm_provider="databricks",
            endpoint=custom_endpoint,
            docs_retriever=docs_retriever
        )
    elif openai_key:
        # Use OpenAI if customer prefers (optional)
        agent = WAFRecommendationAgent(
            llm_provider="openai",
            api_key=openai_key,
            docs_retriever=docs_retriever
        )
    else:
        # Default: Use Databricks Foundation Model API (Anthropic Claude)
        # No API key needed - uses workspace authentication
        agent = WAFRecommendationAgent(
            llm_provider="databricks",
            endpoint="databricks-anthropic-claude-3-5-sonnet",  # Default endpoint
            workspace_client=w,  # Uses workspace auth
            docs_retriever=docs_retriever
        )
    
    print("   ✅ Agent ready (using Databricks Foundation Model)")
    return agent
```

---

## 📚 Databricks Docs Integration (Using Vector Search)

### Using Databricks Vector Search (Recommended)

**Why Databricks Vector Search?**
- ✅ Native Databricks feature - no external dependencies
- ✅ Integrated with Unity Catalog
- ✅ Scalable and performant
- ✅ Works seamlessly with Databricks SQL
- ✅ No additional infrastructure needed

**Architecture**:
```
Databricks Docs → Vector Search Index → Agent Retrieval
```

### Implementation

#### 1. Create Vector Search Index (During Installation)

```python
# install/setup_vector_search.py
from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

def setup_vector_search_index():
    """Create Vector Search index for Databricks docs"""
    w = WorkspaceClient()
    vs_client = VectorSearchClient()
    
    # Create catalog and schema for docs
    catalog_name = "waf_tool"
    schema_name = "docs"
    index_name = "databricks_docs_index"
    
    # Create catalog if not exists
    try:
        w.catalogs.create(catalog_name)
    except:
        pass  # Already exists
    
    # Create schema
    try:
        w.schemas.create(schema_name, catalog_name=catalog_name)
    except:
        pass
    
    # Load Databricks docs
    docs = load_databricks_docs()  # Pre-loaded or scraped
    
    # Create Delta table with docs
    docs_table = f"{catalog_name}.{schema_name}.databricks_docs"
    create_docs_table(w, docs_table, docs)
    
    # Create Vector Search index
    index = vs_client.create_index(
        name=index_name,
        primary_key="doc_id",
        index_type="DELTA_SYNC",
        delta_sync_index_spec={
            "source_table": docs_table,
            "pipeline_type": "TRIGGERED",
            "embedding_source_columns": [
                {
                    "name": "content",
                    "embedding_model_endpoint_name": "databricks-bge-large-en"  # Or customer's endpoint
                }
            ],
            "embedding_vector_columns": [
                {
                    "name": "embedding",
                    "embedding_dimension": 1024
                }
            ]
        }
    )
    
    return index_name
```

#### 2. Docs Retriever Using Vector Search

```python
# agent/docs_retriever.py
from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

class DatabricksDocsRetriever:
    """
    Retrieves Databricks docs using Vector Search
    """
    
    def __init__(self, index_name: str = "waf_tool.docs.databricks_docs_index"):
        self.w = WorkspaceClient()
        self.vs_client = VectorSearchClient()
        self.index_name = index_name
    
    def get_context(self, query: str, waf_id: str = None, top_k: int = 3) -> str:
        """
        Retrieve relevant Databricks docs using Vector Search
        
        Args:
            query: User query or topic
            waf_id: Optional WAF control ID (e.g., R-01-01)
            top_k: Number of documents to retrieve
        
        Returns:
            Relevant documentation context
        """
        # Enhance query with WAF context if provided
        if waf_id:
            query = f"{query} {waf_id} Databricks best practices"
        
        # Search vector index
        results = self.vs_client.search_index(
            index_name=self.index_name,
            query_text=query,
            columns=["doc_id", "title", "content", "url"],
            num_results=top_k
        )
        
        # Format results
        context_parts = []
        for result in results.get("result", {}).get("data_array", []):
            doc_id, title, content, url = result
            context_parts.append(
                f"**{title}**\n{content}\nSource: {url}\n"
            )
        
        return "\n\n".join(context_parts)
    
    def get_waf_specific_docs(self, waf_id: str) -> str:
        """Get documentation specific to a WAF control"""
        # Map WAF IDs to topics
        waf_topics = {
            "R-01-01": "Delta Lake format ACID transactions",
            "R-01-03": "Delta Live Tables DLT data quality",
            "R-01-05": "Model Serving production infrastructure",
            "R-01-06": "Serverless managed services",
            "G-02-01": "Unity Catalog row-level security",
            "CO-01-01": "Delta Lake cost optimization",
            "PE-01-01": "Serverless compute performance",
            # ... more mappings
        }
        
        topic = waf_topics.get(waf_id, "Databricks best practices")
        return self.get_context(topic, waf_id=waf_id)
```

#### 3. Load Databricks Docs (Pre-loaded or Scraped)

```python
# install/load_docs.py
def load_databricks_docs():
    """
    Load Databricks documentation
    Can be pre-loaded in package or scraped during install
    """
    docs = [
        {
            "doc_id": "delta-lake-001",
            "title": "Delta Lake Overview",
            "content": "Delta Lake is an open-source storage layer...",
            "url": "https://docs.databricks.com/en/delta/",
            "category": "reliability",
            "waf_related": ["R-01-01", "CO-01-01"]
        },
        {
            "doc_id": "dlt-001",
            "title": "Delta Live Tables",
            "content": "Delta Live Tables (DLT) is a framework...",
            "url": "https://docs.databricks.com/en/dlt/",
            "category": "reliability",
            "waf_related": ["R-01-03", "R-02-04"]
        },
        # ... more docs
    ]
    
    return docs

def create_docs_table(w: WorkspaceClient, table_name: str, docs: list):
    """Create Delta table with docs for Vector Search"""
    import pandas as pd
    
    # Convert to DataFrame
    df = pd.DataFrame(docs)
    
    # Write to Delta table
    spark = w.spark
    spark_df = spark.createDataFrame(df)
    spark_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
```

#### 4. Update Agent to Use Vector Search

```python
# agent/agent.py
from agent.docs_retriever import DatabricksDocsRetriever

class WAFRecommendationAgent:
    def __init__(self):
        # Use Databricks Vector Search instead of external store
        self.docs_retriever = DatabricksDocsRetriever(
            index_name="waf_tool.docs.databricks_docs_index"
        )
        # ... rest of agent setup
```

### Benefits of Databricks Vector Search

1. **Native Integration**
   - ✅ No external vector store needed
   - ✅ Uses Unity Catalog
   - ✅ Integrated with Databricks SQL

2. **Performance**
   - ✅ Fast semantic search
   - ✅ Scalable to large doc sets
   - ✅ Optimized for Databricks infrastructure

3. **Simplicity**
   - ✅ No additional infrastructure
   - ✅ No external API keys (for vector store)
   - ✅ Everything in one platform

4. **Cost**
   - ✅ No external service costs
   - ✅ Uses Databricks compute
   - ✅ Efficient resource usage

### Alternative: Use Databricks Foundation Model APIs

If customer doesn't have Vector Search enabled, we can use:
- Databricks Foundation Model APIs for embeddings
- Store in Delta table
- Use SQL-based similarity search (less optimal but works)

---

## 🔐 Secrets Management

### Customer Provides (Optional for Agent)

**Via Databricks Secrets**:
```
1. Customer creates secret scope: `waf-tool`
2. Adds secrets:
   - `waf-tool/OPENAI_API_KEY` (or)
   - `waf-tool/ANTHROPIC_API_KEY`
3. App reads from secrets automatically
```

**Via App Settings** (Marketplace):
```
1. Customer enters API key in installation form
2. Stored securely as app secret
3. App accesses via environment variable
```

---

## 📦 Marketplace Listing

### Marketplace Metadata

```yaml
# marketplace-listing.yml
name: WAF Assessment Tool
category: Governance & Compliance
description: |
  Automated Well-Architected Framework assessment for Databricks.
  Get real-time scores, recommendations, and AI-powered guidance.

features:
  - Real-time WAF scoring across 4 pillars
  - AI-powered recommendation agent
  - Interactive dashboard
  - Databricks documentation integration
  - REST API for programmatic access

requirements:
  - Unity Catalog enabled
  - SQL Warehouse access
  - System Tables read permission

optional:
  - OpenAI or Anthropic API key (for agent)

screenshots:
  - dashboard.png
  - agent-chat.png
  - waf-guide.png

documentation_url: https://github.com/databricks/waf-assessment-tool
support_url: https://github.com/databricks/waf-assessment-tool/issues
```

---

## 🚀 Deployment Architecture

```
Customer's Databricks Workspace:
┌─────────────────────────────────────────────────────┐
│  Databricks App (waf-assessment-tool)              │
│  ┌──────────────────────────────────────────────┐  │
│  │  Streamlit App (app/app.py)                   │  │
│  │  - Dashboard view                             │  │
│  │  - WAF Guide                                  │  │
│  │  - Agent Chat (if API key provided)           │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  REST API (api/main.py)                       │  │
│  │  - /api/v1/scores                             │  │
│  │  - /api/v1/metrics                            │  │
│  │  - /api/v1/chat (agent)                      │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  WAF Recommendation Agent                     │  │
│  │  - LangChain agent                            │  │
│  │  - Databricks docs (pre-loaded)               │  │
│  │  - LLM (OpenAI/Anthropic)                     │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Dashboard (WAF_ASSESSMENTv1.6)              │  │
│  │  - Deployed during install                     │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
         │
         ▼
  System Tables (queries)
```

---

## ✅ Installation Checklist

### What Happens During Install

1. ✅ **Dashboard Deployment**
   - Creates dashboard from JSON
   - Configures SQL Warehouse
   - Publishes dashboard

2. ✅ **App Configuration**
   - Sets environment variables
   - Configures dashboard embedding
   - Sets up workspace URLs

3. ✅ **Agent Setup** (if API key provided)
   - Loads Databricks docs
   - Initializes vector store
   - Sets up LLM connection
   - Tests agent

4. ✅ **API Setup**
   - Starts REST API server
   - Configures routes
   - Sets up authentication

5. ✅ **Finalization**
   - Displays access URLs
   - Shows configuration status
   - Provides next steps

---

## 📝 Customer Experience

### Installation (Marketplace)

```
1. Customer clicks "Install" in Marketplace
2. Selects workspace
3. Clicks "Deploy" (no API keys needed!)
4. Installation runs automatically (~2-3 minutes)
5. ✅ Success! App is ready
6. Customer clicks "Open App"
7. Sees dashboard + WAF Guide + Agent (ready to use!)
```

**No API keys required** - Agent uses Databricks Foundation Model APIs automatically!

### First Use

```
1. Customer opens app
2. Sees dashboard with WAF scores
3. Can browse WAF Guide for details
4. Can immediately ask agent questions (no setup needed!):
   - "Why is my reliability score low?"
   - "How do I increase DLT usage?"
   - "What's the best practice for Delta tables?"
5. Agent provides answers with docs references
   - Uses Databricks Foundation Model (Anthropic Claude)
   - Retrieves docs from Vector Search
   - Provides intelligent recommendations
```

---

## 🔧 Requirements File

### `requirements.txt`

```txt
# Core
streamlit>=1.28.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# Databricks
databricks-sdk>=0.20.0
databricks-sql-connector>=3.0.0

# Agent (Uses Databricks Foundation Model - No external APIs needed!)
langchain>=0.1.0
langchain-community>=0.0.20  # For ChatDatabricks
# Optional overrides (only if customer wants to use external APIs):
# langchain-openai>=0.0.5
# openai>=1.0.0
# anthropic>=0.7.0

# Databricks Vector Search (Native - No external dependencies needed!)
# databricks-vector-search (when available) or use SQL-based approach
# Alternative: Use Databricks Foundation Model APIs for embeddings

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
```

---

## 📦 Package Size Considerations

### What Gets Packaged

1. **Code**: ~5-10 MB
2. **Databricks Docs** (pre-loaded): ~50-100 MB
3. **Dashboard JSON**: ~1 MB
4. **Total**: ~60-110 MB

### Optimization

- Compress docs
- Use efficient vector store format
- Lazy load docs (load on first agent use)

---

## 🎯 Success Criteria

### Installation Success

- ✅ Dashboard deployed and accessible
- ✅ App runs without errors
- ✅ REST API responds
- ✅ Agent works (if API key provided)
- ✅ All features functional

### Customer Experience

- ✅ One-click installation
- ✅ No manual configuration needed
- ✅ Clear success/failure messages
- ✅ Easy access to app
- ✅ Agent works out of the box (if API key provided)

---

## 🚀 Next Steps for Implementation

1. **Package App Structure**
   - Organize code into app structure
   - Create `databricks-app.yml`
   - Prepare `requirements.txt`

2. **Create Installation Script**
   - Dashboard deployment
   - App configuration
   - Agent setup

3. **Prepare Marketplace Listing**
   - Screenshots
   - Documentation
   - Metadata

4. **Test Installation**
   - Test on clean workspace
   - Verify all features work
   - Test with/without API keys

5. **Submit to Marketplace**
   - Follow Databricks Marketplace guidelines
   - Submit for review
   - Publish

---

**Last Updated**: February 2026  
**Status**: Planning - Ready for Implementation  
**Target**: One-click installation from Marketplace or Git
