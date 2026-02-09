# 🚀 WAF Assessment Tool - MVP Extension Implementation Plan

## 🎯 Customer-Side Deployment Model

**Important**: All components deploy on the customer's Databricks workspace. We provide:
- ✅ Dashboard (existing)
- ✅ REST API service (new)
- ✅ MCP service (new, optional)
- ✅ Context data provider (new) - **Just data, NOT an agent**

**We do NOT deploy**:
- ❌ AI agents (customer deploys separately - e.g., LakeForge)
- ❌ Agent orchestration (customer manages)
- ❌ Agent runtime (customer provides)

**Integration Pattern**: 
- WAF Tool provides: REST API endpoint (`/api/v1/context`) with structured JSON data
- Customer deploys: Their own AI agent (LakeForge, custom agent, etc.) separately
- Agent calls: `/api/v1/context` to get WAF assessment data
- Agent uses: Context to build WAF-compliant solutions

**Deployment Architecture**:
```
Customer's Databricks Workspace:
┌─────────────────────────────────────────────────┐
│  WAF Assessment Tool (What we deploy)          │
│  - Dashboard                                    │
│  - REST API                                    │
│  - WAF Recommendation Agent (Chat Interface)   │ ← NEW
│  - MCP Service (optional)                      │
│  - Context Provider (/api/v1/context)         │
└─────────────────────────────────────────────────┘
         │                    │
         │                    │
    ┌────▼────┐        ┌─────▼─────┐
    │  User   │        │  External  │
    │  Chat   │        │  Agents    │
    │         │        │ (LakeForge)│
    │ Asks:   │        │            │
    │ "Why is │        │ Calls:     │
    │  score  │        │ /api/v1/   │
    │  low?"  │        │ context    │
    └─────────┘        └────────────┘
```

**WAF Recommendation Agent Flow**:
1. User asks: "Why is my reliability score low?"
2. Agent gets WAF scores → Identifies failing metrics
3. Agent retrieves Databricks docs → DLT, Model Serving, etc.
4. Agent generates recommendations → Combines scores + docs
5. Agent answers: "Your reliability is 38% because..."
6. User asks follow-up: "How do I increase DLT usage?"
7. Agent provides detailed steps with docs references

---

## 📊 Current Architecture

### What We Have Today

```
┌─────────────────────────────────────────────────────────┐
│              Current WAF Assessment Tool                │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Lakeview Dashboard (WAF_ASSESSMENTv1.6)        │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │  13 Datasets (SQL Queries)                │ │   │
│  │  │  - 3 per pillar × 4 pillars = 12         │ │   │
│  │  │  - 1 summary dataset                      │ │   │
│  │  │                                            │ │   │
│  │  │  Each dataset:                            │ │   │
│  │  │  • Queries System Tables                  │ │   │
│  │  │  • Calculates scores using CTEs           │ │   │
│  │  │  • Returns structured data                │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  │  ┌────────────────────────────────────────────┐ │   │
│  │  │  Charts & Tables (Visualization)           │ │   │
│  │  │  - Pillar scores                         │ │   │
│  │  │  - Individual metrics                     │ │   │
│  │  │  - Principle breakdowns                   │ │   │
│  │  └────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Streamlit App (waf-automation-tool)            │   │
│  │  - Embeds dashboard                             │   │
│  │  - WAF Guide sidebar                            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Current Data Flow

1. **User opens Dashboard** → Dashboard loads
2. **Dashboard executes SQL queries** → Queries System Tables
3. **System Tables return data** → Datasets calculate scores
4. **Charts display results** → User sees scores

**Key Point**: All calculation logic is **embedded in SQL queries** within the dashboard JSON file.

---

## 🎯 MVP Extension Goals

Extend the tool to support:
1. **REST API** - Programmatic access to WAF scores
2. **MCP Service** - AI assistant integration
3. **AI Agent Context Provider** - Structured context for agents (LakeForge pattern)

**Without modifying existing dashboard or app code.**

---

## 🏗️ What Needs to Be Built

### Phase 1: Extract Query Logic (Foundation)

**Problem**: Calculation logic is currently embedded in dashboard JSON SQL queries.

**Solution**: Extract SQL queries into reusable Python functions.

#### 1.1 Create Query Library Module

**File**: `waf_core/queries.py`

```python
"""
WAF Assessment Query Library
Extracts SQL queries from dashboard into reusable functions
"""

def get_reliability_scores():
    """Execute Reliability pillar queries and return structured data"""
    # Extract SQL from dashboard dataset: waf_controls_r
    # Execute via Databricks SQL API
    # Return: List of metrics with scores
    
def get_governance_scores():
    """Execute Governance pillar queries"""
    
def get_cost_scores():
    """Execute Cost Optimization pillar queries"""
    
def get_performance_scores():
    """Execute Performance Efficiency pillar queries"""
    
def get_all_scores():
    """Get scores for all pillars"""
    return {
        "reliability": get_reliability_scores(),
        "governance": get_governance_scores(),
        "cost": get_cost_scores(),
        "performance": get_performance_scores()
    }
```

**What this does**:
- Reads SQL queries from dashboard JSON (or maintains separate query definitions)
- Executes queries via Databricks SQL API
- Returns structured Python dictionaries (not just raw SQL results)

**Reuses**: Existing SQL query logic from dashboard datasets

---

### Phase 2: REST API Service

**File**: `waf_api/main.py` (FastAPI application)

#### 2.1 API Endpoints

```python
from fastapi import FastAPI
from waf_core.queries import get_all_scores, get_pillar_score

app = FastAPI()

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/scores")
def get_scores():
    """Get overall WAF scores for all pillars"""
    scores = get_all_scores()
    return {
        "reliability": scores["reliability"]["completion_percent"],
        "governance": scores["governance"]["completion_percent"],
        "cost": scores["cost"]["completion_percent"],
        "performance": scores["performance"]["completion_percent"]
    }

@app.get("/api/v1/scores/{pillar}")
def get_pillar_score(pillar: str):
    """Get score for specific pillar"""
    # pillar: reliability, governance, cost, performance
    return get_pillar_score(pillar)

@app.get("/api/v1/metrics")
def get_all_metrics():
    """Get all WAF control metrics"""
    scores = get_all_scores()
    all_metrics = []
    for pillar_data in scores.values():
        all_metrics.extend(pillar_data["metrics"])
    return all_metrics

@app.get("/api/v1/metrics/{waf_id}")
def get_metric_details(waf_id: str):
    """Get details for specific metric (e.g., R-01-01)"""
    # Find metric across all pillars
    # Return detailed information
```

#### 2.2 Authentication

```python
from databricks.sdk import WorkspaceClient

def get_databricks_client(token: str, workspace_url: str):
    """Create authenticated Databricks client"""
    return WorkspaceClient(
        host=workspace_url,
        token=token
    )
```

#### 2.3 Deployment Options

**Option A: Databricks Jobs**
- Run as scheduled or on-demand job
- Expose via Databricks API Gateway or reverse proxy

**Option B: Separate Compute**
- Deploy FastAPI app on separate server/container
- Connect to Databricks via API

**Option C: Databricks Apps (Future)**
- If Databricks supports API endpoints in Apps

---

### Phase 3: MCP Service

**File**: `waf_mcp/server.py`

#### 3.1 MCP Server Implementation

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
from waf_core.queries import get_all_scores

server = Server("waf-assessment")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_waf_scores",
            description="Get overall WAF assessment scores for all pillars",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_pillar_score",
            description="Get score for a specific WAF pillar",
            inputSchema={
                "type": "object",
                "properties": {
                    "pillar": {
                        "type": "string",
                        "enum": ["reliability", "governance", "cost", "performance"]
                    }
                },
                "required": ["pillar"]
            }
        ),
        Tool(
            name="get_failing_metrics",
            description="Get all WAF control metrics that are currently failing",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_metric_details",
            description="Get detailed information about a specific WAF control",
            inputSchema={
                "type": "object",
                "properties": {
                    "waf_id": {
                        "type": "string",
                        "description": "WAF identifier (e.g., R-01-01, G-02-03)"
                    }
                },
                "required": ["waf_id"]
            }
        ),
        Tool(
            name="get_recommendations",
            description="Get actionable recommendations to improve WAF scores",
            inputSchema={
                "type": "object",
                "properties": {
                    "pillar": {
                        "type": "string",
                        "enum": ["reliability", "governance", "cost", "performance"],
                        "description": "Optional: Filter by pillar"
                    }
                }
            }
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_waf_scores":
        scores = get_all_scores()
        return [TextContent(
            type="text",
            text=f"WAF Scores:\n"
                 f"Reliability: {scores['reliability']['completion_percent']}%\n"
                 f"Governance: {scores['governance']['completion_percent']}%\n"
                 f"Cost: {scores['cost']['completion_percent']}%\n"
                 f"Performance: {scores['performance']['completion_percent']}%"
        )]
    # ... other tool handlers
```

#### 3.2 MCP Server Deployment

- Run as standalone Python service
- Expose via stdio or HTTP transport
- Can be integrated with Claude Desktop, Cursor, etc.

---

### Phase 4: WAF Recommendation Agent (Conversational AI Agent)

**Key Requirement**: Build an AI agent that:
1. ✅ Understands WAF scores from assessments
2. ✅ Adds context from Databricks documentation
3. ✅ Provides intelligent recommendations based on scores
4. ✅ Answers follow-up questions about WAF scores and recommendations

**This is a conversational/recommendation agent** (different from code generation agents like LakeForge).

**Files**: 
- `waf_agent/agent.py` - Main agent implementation
- `waf_agent/docs_retriever.py` - Databricks docs context retrieval
- `waf_agent/recommendations.py` - Recommendation engine
- `waf_agent/chat_interface.py` - Conversational interface

#### 4.1 Agent Architecture

```python
# waf_agent/agent.py
from langchain.agents import AgentExecutor
from langchain.llms import OpenAI  # or Claude, etc.
from waf_core.queries import get_all_scores
from waf_agent.docs_retriever import get_databricks_docs_context
from waf_agent.recommendations import generate_recommendations

class WAFRecommendationAgent:
    """
    Conversational AI agent that:
    - Understands WAF scores
    - Retrieves Databricks docs context
    - Provides recommendations
    - Answers follow-up questions
    
    Uses Databricks Foundation Model APIs (Anthropic Claude) by default
    No API keys required!
    """
    
    def __init__(self, workspace_client=None, endpoint="databricks-anthropic-claude-3-5-sonnet"):
        from databricks.sdk import WorkspaceClient
        from langchain_community.chat_models import ChatDatabricks
        
        # Use Databricks Foundation Model (default)
        # No API key needed - uses workspace authentication
        self.w = workspace_client or WorkspaceClient()
        self.llm = ChatDatabricks(
            endpoint=endpoint,
            databricks_workspace_url=self.w.config.host,
            databricks_token=self.w.config.token
        )
        
        self.tools = [
            self.get_waf_scores_tool(),
            self.get_databricks_docs_tool(),
            self.get_recommendations_tool()
        ]
        self.agent = self._create_agent()
    
    def get_waf_scores_tool(self):
        """Tool to get current WAF scores"""
        def get_scores(query: str) -> str:
            scores = get_all_scores()
            return f"""
            Current WAF Scores:
            - Reliability: {scores['reliability']['completion_percent']}%
            - Governance: {scores['governance']['completion_percent']}%
            - Cost: {scores['cost']['completion_percent']}%
            - Performance: {scores['performance']['completion_percent']}%
            
            Failing Metrics:
            {self._format_failing_metrics(scores)}
            """
        return get_scores
    
    def get_databricks_docs_tool(self):
        """Tool to retrieve relevant Databricks documentation"""
        def get_docs(topic: str) -> str:
            # Retrieve relevant docs based on topic
            # e.g., "Delta Lake", "DLT", "Unity Catalog", etc.
            docs = get_databricks_docs_context(topic)
            return docs
        return get_docs
    
    def get_recommendations_tool(self):
        """Tool to generate recommendations"""
        def get_recommendations(pillar: str = None) -> str:
            scores = get_all_scores()
            recommendations = generate_recommendations(scores, pillar)
            return recommendations
        return get_recommendations
    
    def chat(self, user_message: str) -> str:
        """Main chat interface - answers questions about WAF scores"""
        # Agent uses tools to:
        # 1. Get current WAF scores
        # 2. Retrieve relevant Databricks docs
        # 3. Generate recommendations
        # 4. Answer follow-up questions
        response = self.agent.run(
            input=user_message,
            tools=self.tools
        )
        return response
```

#### 4.2 Databricks Docs Integration (Using Vector Search)

**Why Databricks Vector Search?**
- ✅ Native Databricks feature - no external dependencies
- ✅ Integrated with Unity Catalog
- ✅ Scalable and performant
- ✅ Works seamlessly with Databricks SQL
- ✅ No additional infrastructure needed

```python
# waf_agent/docs_retriever.py
from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

class DatabricksDocsRetriever:
    """
    Retrieves relevant Databricks documentation using Vector Search
    """
    
    def __init__(self, index_name: str = "waf_tool.docs.databricks_docs_index"):
        self.w = WorkspaceClient()
        self.vs_client = VectorSearchClient()
        self.index_name = index_name
    
    def get_context(self, topic: str, waf_id: str = None, top_k: int = 3) -> str:
        """
        Retrieve relevant Databricks docs using Vector Search
        
        Topics: "Delta Lake", "DLT", "Unity Catalog", "Serverless", etc.
        """
        # Enhance query with WAF context
        query = f"{topic} {waf_id} Databricks best practices" if waf_id else topic
        
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
            # ... more mappings
        }
        
        topic = waf_topics.get(waf_id, "Databricks best practices")
        return self.get_context(topic, waf_id=waf_id)
```

**Vector Search Index Setup** (during installation):
```python
# install/setup_vector_search.py
def setup_vector_search_index():
    """Create Vector Search index for Databricks docs"""
    # Create catalog and schema
    # Load docs into Delta table
    # Create Vector Search index with embeddings
    # Return index name
```

#### 4.3 Recommendation Engine

```python
# waf_agent/recommendations.py
def generate_recommendations(scores: dict, pillar: str = None) -> str:
    """
    Generate intelligent recommendations based on WAF scores
    Combines:
    - Current scores
    - Failing metrics
    - Databricks best practices
    - Actionable steps
    """
    recommendations = []
    
    if pillar:
        pillar_data = scores[pillar]
        for metric in pillar_data['failing_metrics']:
            rec = {
                'waf_id': metric['waf_id'],
                'issue': f"Current score {metric['current_score']}% is below threshold {metric['threshold']}%",
                'recommendation': metric['recommendation'],
                'action_items': metric['action_items'],
                'docs_reference': get_databricks_docs_context(metric['waf_id'])
            }
            recommendations.append(rec)
    else:
        # Generate recommendations for all failing metrics
        for pillar_name, pillar_data in scores.items():
            for metric in pillar_data.get('failing_metrics', []):
                recommendations.append(...)
    
    return format_recommendations(recommendations)
```

#### 4.4 Chat Interface

```python
# waf_agent/chat_interface.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
agent = WAFRecommendationAgent()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []  # Databricks docs sources

@app.post("/api/v1/chat")
def chat(request: ChatRequest):
    """Chat endpoint for WAF recommendation agent"""
    response = agent.chat(request.message)
    return ChatResponse(
        response=response,
        sources=agent.get_sources()  # Which docs were used
    )

# Example usage:
# User: "Why is my reliability score low?"
# Agent: 
#   1. Gets WAF scores → Sees Reliability is 38%
#   2. Identifies failing metrics (R-01-03, R-01-05, etc.)
#   3. Retrieves Databricks docs on DLT, Model Serving
#   4. Provides recommendations with code examples
#   5. Answers follow-up: "How do I increase DLT usage?"
```

#### 4.5 Agent Deployment

**Deployment Options**:

1. **Streamlit Chat Interface** (Recommended for MVP):
   - Add chat widget to existing Streamlit app
   - Agent runs in background
   - User can ask questions about WAF scores

2. **REST API Endpoint**:
   - `/api/v1/chat` endpoint
   - Can be integrated into any UI
   - Supports conversational flow

3. **Databricks App Integration**:
   - Embed chat interface in Databricks App
   - Agent accessible alongside dashboard

#### 4.6 Example Conversations

```
User: "What's my WAF score?"
Agent: "Your current WAF scores are:
- Reliability: 38%
- Governance: 65%
- Cost: 45%
- Performance: 72%

Your Reliability score is low. The main issues are:
- R-01-03: DLT usage is only 25% (threshold: 30%)
- R-01-05: Model Serving usage is 15% (threshold: 20%)

Would you like recommendations to improve these?"

User: "How do I increase DLT usage?"
Agent: "To increase DLT usage, here are the steps:

1. Migrate existing pipelines to DLT:
   [Retrieves Databricks docs on DLT migration]
   [Provides code example]

2. Use DLT for new data quality checks:
   [Retrieves docs on DLT data quality]
   [Shows example]

Based on Databricks documentation, DLT provides automatic
data quality checks and schema evolution. Here's how to get started..."

User: "What's the best practice for Delta tables?"
Agent: [Retrieves Delta Lake docs]
       [Provides best practices]
       [Shows how it relates to R-01-01 metric]
```

---

### Phase 5: Context Provider for External Agents (Optional)

**File**: `waf_context/provider.py`

#### 5.1 Context Format (Optimized for LLM)

```python
def get_waf_context(workspace_id: str) -> dict:
    """
    Generate structured context for AI agents (LakeForge pattern)
    Returns JSON optimized for LLM consumption
    
    NOTE: This is just a data provider function.
    The actual AI agent (LakeForge, etc.) is deployed separately by the customer.
    """
    scores = get_all_scores()
    
    return {
        "workspace_id": workspace_id,
        "assessment_timestamp": datetime.now().isoformat(),
        "overall_score": calculate_overall_score(scores),
        "pillars": {
            "reliability": {
                "score": scores["reliability"]["completion_percent"],
                "status": "needs_improvement",  # or "good", "excellent"
                "failing_metrics": [
                    {
                        "waf_id": "R-01-03",
                        "principle": "Design for failure",
                        "best_practice": "Automatically rescue invalid data",
                        "current_score": 25.0,
                        "threshold": 30.0,
                        "gap": 5.0,
                        "recommendation": "Increase DLT usage to 30% or more",
                        "action_items": [
                            "Migrate existing pipelines to DLT",
                            "Use DLT for new data quality checks"
                        ],
                        "code_example": "-- Example: Create DLT pipeline\nCREATE OR REFRESH STREAMING LIVE TABLE..."
                    }
                ],
                "recommendations": [
                    "Focus on increasing DLT adoption for data quality",
                    "Consider migrating legacy pipelines to DLT"
                ]
            },
            # ... other pillars
        },
        "priority_actions": [
            # Top 5 actions across all pillars
        ],
        "compliance_summary": {
            "total_controls": 32,
            "passing_controls": 18,
            "failing_controls": 14,
            "compliance_percentage": 56.25
        }
    }
```

#### 4.2 Context API Endpoint

```python
@app.get("/api/v1/context")
def get_context():
    """Get WAF context for AI agents (LakeForge pattern)
    
    This endpoint provides structured data that external AI agents can consume.
    The agent itself (LakeForge, custom agent, etc.) is deployed separately.
    """
    return get_waf_context(workspace_id)
```

**What this provides** (for external agents like LakeForge):
- ✅ Structured JSON endpoint optimized for LLM consumption
- ✅ Includes scores, recommendations, action items, code examples
- ✅ Can be consumed by external agents (LakeForge, custom agents, etc.)

**Note**: This is separate from the WAF Recommendation Agent (Phase 4).
- Phase 4: Conversational agent for users (deployed with WAF Tool)
- Phase 5: Context data for external code generation agents (LakeForge, etc.)

---

## 📋 Implementation Checklist

### Step 1: Extract Query Logic (Week 1)

- [ ] **1.1** Create `waf_core/` directory structure
- [ ] **1.2** Extract SQL queries from dashboard JSON
- [ ] **1.3** Create Python functions that execute queries via Databricks SQL API
- [ ] **1.4** Test query functions return correct data structure
- [ ] **1.5** Add error handling and logging

**Files to create**:
- `waf_core/__init__.py`
- `waf_core/queries.py` - Query execution functions
- `waf_core/databricks_client.py` - Databricks API client wrapper
- `waf_core/models.py` - Data models (PillarScore, Metric, etc.)

**Reuses**: SQL query logic from dashboard (can read from JSON or maintain separately)

---

### Step 2: Build REST API (Week 2)

- [ ] **2.1** Set up FastAPI project structure
- [ ] **2.2** Implement authentication (Databricks tokens)
- [ ] **2.3** Create core endpoints:
  - [ ] `/api/v1/health`
  - [ ] `/api/v1/scores`
  - [ ] `/api/v1/scores/{pillar}`
  - [ ] `/api/v1/metrics`
  - [ ] `/api/v1/metrics/{waf_id}`
  - [ ] `/api/v1/recommendations`
  - [ ] `/api/v1/context` (for AI agents)
- [ ] **2.4** Add request validation and error handling
- [ ] **2.5** Add API documentation (OpenAPI/Swagger)
- [ ] **2.6** Deploy API service
- [ ] **2.7** Test all endpoints

**Files to create**:
- `waf_api/__init__.py`
- `waf_api/main.py` - FastAPI application
- `waf_api/routes/` - API route handlers
- `waf_api/auth.py` - Authentication logic
- `waf_api/config.py` - Configuration
- `requirements.txt` - Python dependencies

**Dependencies**:
- `fastapi`
- `databricks-sdk` or `databricks-sql-connector`
- `pydantic` (for data validation)

---

### Step 3: Build MCP Service (Week 2-3)

- [ ] **3.1** Set up MCP server project
- [ ] **3.2** Implement MCP tools (5 tools minimum)
- [ ] **3.3** Connect to query library
- [ ] **3.4** Test with Claude Desktop or Cursor
- [ ] **3.5** Add error handling
- [ ] **3.6** Deploy MCP server

**Files to create**:
- `waf_mcp/__init__.py`
- `waf_mcp/server.py` - MCP server implementation
- `waf_mcp/tools.py` - Tool definitions and handlers

**Dependencies**:
- `mcp` (Model Context Protocol SDK)

---

### Step 4: Build WAF Recommendation Agent (Week 3-4)

**Key Requirement**: Conversational AI agent that understands scores, adds Databricks docs context, and answers questions.

- [ ] **4.1** Set up LLM framework (LangChain with Databricks Foundation Model)
  - [ ] Use `ChatDatabricks` from `langchain_community`
  - [ ] Configure to use `databricks-anthropic-claude-3-5-sonnet` endpoint
  - [ ] Use workspace authentication (no API keys needed!)
- [ ] **4.2** Create agent architecture with tools:
  - [ ] Tool: Get WAF scores
  - [ ] Tool: Retrieve Databricks docs
  - [ ] Tool: Generate recommendations
- [ ] **4.3** Build Databricks docs retriever (using Vector Search):
  - [ ] Load/scrape Databricks documentation
  - [ ] Create Delta table with docs
  - [ ] Create Vector Search index (during installation)
  - [ ] Implement semantic search using Vector Search API
- [ ] **4.4** Build recommendation engine:
  - [ ] Analyze failing metrics
  - [ ] Combine scores + docs context
  - [ ] Generate actionable recommendations
- [ ] **4.5** Create chat interface:
  - [ ] REST API endpoint (`/api/v1/chat`)
  - [ ] Streamlit chat widget (integrate into app)
  - [ ] Conversation memory/history
- [ ] **4.6** Test agent with sample questions:
  - [ ] "What's my WAF score?"
  - [ ] "Why is reliability low?"
  - [ ] "How do I increase DLT usage?"
  - [ ] Follow-up questions
- [ ] **4.7** Deploy agent (Streamlit app or separate service)

**Files to create**:
- `waf_agent/__init__.py`
- `waf_agent/agent.py` - Main agent implementation
- `waf_agent/docs_retriever.py` - Databricks docs retrieval
- `waf_agent/recommendations.py` - Recommendation engine
- `waf_agent/chat_interface.py` - Chat API/UI
- `waf_agent/memory.py` - Conversation memory

**Dependencies**:
- `langchain` or `llama-index` (agent framework)
- `langchain-community` (for `ChatDatabricks` - Databricks Foundation Model integration)
- `databricks-sdk` (for workspace authentication)
- `databricks-vector-search` (Vector Search client - native Databricks)
- `databricks-docs-scraper` (or manual docs collection)

**No external API keys needed!**
- ✅ Uses Databricks Foundation Model APIs (Anthropic Claude) by default
- ✅ Uses workspace authentication (no API keys)
- ✅ Using Databricks Vector Search eliminates need for external vector stores
- ✅ Optional: Customer can override with custom endpoint if preferred

---

### Step 5: Build Context Provider for External Agents (Week 4) - Optional

**For external agents like LakeForge** (separate from recommendation agent):

- [ ] **5.1** Design context JSON schema (optimized for LLM consumption)
- [ ] **5.2** Implement context generation function
- [ ] **5.3** Add code examples to context (SQL examples, best practices)
- [ ] **5.4** Integrate with REST API (`/api/v1/context` endpoint)
- [ ] **5.5** Document how external agents can consume the context

**What we build**:
- ✅ Context generation function
- ✅ REST API endpoint that returns context JSON
- ✅ Documentation for agent integration

**What we do NOT build**:
- ❌ AI agent code
- ❌ Agent runtime/deployment
- ❌ Agent orchestration logic

**Files to create**:
- `waf_context/__init__.py`
- `waf_context/provider.py` - Context generation
- `waf_context/recommendations.py` - Recommendation logic
- `waf_context/examples.py` - Code examples database

---

### Step 5: Testing & Documentation (Week 4)

- [ ] **5.1** Write unit tests for query functions
- [ ] **5.2** Write integration tests for API
- [ ] **5.3** Test MCP server with AI assistants
- [ ] **5.4** Test context provider with LakeForge (if available)
- [ ] **5.5** Write API documentation
- [ ] **5.6** Write MCP integration guide
- [ ] **5.7** Create example integrations

**Files to create**:
- `tests/` - Test suite
- `docs/API.md` - API documentation
- `docs/MCP_INTEGRATION.md` - MCP setup guide
- `examples/` - Example integrations

---

## 🔧 Technical Architecture

### New Components (No Changes to Existing)

```
┌─────────────────────────────────────────────────────────┐
│              Existing (No Changes)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Lakeview Dashboard                               │   │
│  │  Streamlit App                                    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              New Extensions (MVP)                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  waf_core/ (Query Library)                       │   │
│  │  - queries.py: Execute SQL queries               │   │
│  │  - databricks_client.py: API client              │   │
│  │  - models.py: Data models                        │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
│        ┌─────────────────┼─────────────────┐           │
│        │                 │                 │           │
│        ▼                 ▼                 ▼           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │ REST API │    │ MCP Svc  │    │ Context │           │
│  │ (FastAPI)│    │ (MCP SDK)│    │Provider │           │
│  └──────────┘    └──────────┘    └──────────┘           │
│        │                 │                 │           │
│        └─────────────────┴─────────────────┘           │
│                          │                               │
│                          ▼                               │
│              Databricks System Tables                   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow (Extended)

```
1. User/Agent/System → REST API / MCP / Context Provider
2. Extension Service → waf_core/queries.py
3. Query Library → Databricks SQL API
4. SQL API → System Tables
5. System Tables → Query Results
6. Query Library → Structured Python Objects
7. Extension Service → JSON Response / MCP Response / Context JSON
8. User/Agent/System → Receives data
```

---

## 📦 Dependencies

### Python Packages

```txt
# Core
databricks-sdk>=0.20.0
databricks-sql-connector>=3.0.0

# API
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# Agent Framework
langchain>=0.1.0
langchain-community>=0.0.20  # For ChatDatabricks (Databricks Foundation Model)
# No external LLM APIs needed - uses Databricks Foundation Model by default!
# Optional: langchain-openai>=0.0.5  # Only if customer wants to override

# Vector Store (for Databricks docs)
chromadb>=0.4.0
# or pinecone-client>=2.2.0

# Embeddings
langchain-openai-embeddings>=0.0.3

# MCP
mcp>=0.1.0  # (when available)

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0  # for docs scraping (optional)
```

---

## 🚀 Deployment Strategy (Customer-Side Deployment)

**All components deploy on customer's Databricks workspace.**

### Option 1: Databricks Jobs (Recommended for MVP)

- Deploy API as Databricks Job
- Use Databricks SQL Warehouse for queries
- Expose via Databricks API Gateway or reverse proxy
- **Customer deploys**: Dashboard + API service
- **Customer deploys separately**: Their AI agent (LakeForge, custom, etc.)

### Option 2: Separate Compute

- Deploy FastAPI app on separate server (customer's infrastructure)
- Connect to Databricks via API
- More flexible but requires customer infrastructure
- **Customer deploys**: Dashboard + API service on their compute
- **Customer deploys separately**: Their AI agent

### Option 3: Hybrid

- Query library runs in Databricks (Jobs)
- API runs on separate compute (customer's choice)
- MCP server runs locally or in container (customer's choice)
- **Customer deploys**: All WAF components
- **Customer deploys separately**: Their AI agent

### Deployment Model for Context Provider

```
┌─────────────────────────────────────────────────────────┐
│         Customer's Databricks Workspace                  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  WAF Assessment Tool (What we deploy)             │   │
│  │  - Dashboard                                      │   │
│  │  - REST API (/api/v1/context)                    │   │
│  │  - MCP Service (optional)                        │   │
│  └───────────────────┬───────────────────────────────┘   │
│                      │                                    │
│                      │ Provides context data              │
│                      │                                    │
│  ┌───────────────────▼───────────────────────────────┐   │
│  │  Customer's AI Agent (Deployed separately)       │   │
│  │  - LakeForge                                      │   │
│  │  - Custom agent                                   │   │
│  │  - Other AI tools                                │   │
│  │                                                   │   │
│  │  Calls: GET /api/v1/context                      │   │
│  │  Uses: Context to build WAF-compliant solutions  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Key Points**:
- ✅ WAF Tool provides data/context only
- ✅ Customer deploys their own AI agent separately
- ✅ Agent consumes WAF context via API
- ✅ No agent code in WAF Tool deployment

---

## ✅ Success Criteria (MVP)

1. **REST API**:
   - ✅ All core endpoints working
   - ✅ Returns correct WAF scores
   - ✅ Authentication working
   - ✅ Can be called from external systems

2. **MCP Service**:
   - ✅ 5+ tools implemented
   - ✅ Can query WAF data via AI assistant
   - ✅ Returns structured responses

3. **WAF Recommendation Agent**:
   - ✅ Conversational AI agent deployed with WAF Tool
   - ✅ Understands WAF scores from assessments
   - ✅ Retrieves and uses Databricks documentation context
   - ✅ Provides intelligent recommendations based on scores
   - ✅ Answers follow-up questions about WAF scores and recommendations
   - ✅ Available via chat interface (Streamlit or REST API)

4. **Context Provider** (For External Agents - Optional):
   - ✅ Generates structured JSON context
   - ✅ Includes scores, recommendations, action items
   - ✅ Exposes via REST API endpoint (`/api/v1/context`)
   - ✅ Can be consumed by external AI agents (LakeForge, custom agents)

4. **No Breaking Changes**:
   - ✅ Existing dashboard unchanged
   - ✅ Existing app unchanged
   - ✅ All existing functionality preserved

---

## 📝 Next Steps After MVP

1. **Historical Tracking**: Store scores over time
2. **Multi-workspace Support**: Aggregate across workspaces
3. **Webhooks**: Event-driven notifications
4. **CLI Tool**: Command-line interface
5. **SDK**: Python/JavaScript libraries

---

**Last Updated**: February 2026  
**Status**: Planning - Ready for Implementation  
**Estimated MVP Timeline**: 4-5 weeks
- Week 1: Extract query logic
- Week 2: Build REST API
- Week 3: Build MCP service
- Week 3-4: Build WAF Recommendation Agent (with Databricks docs integration)
- Week 4-5: Testing, documentation, context provider (optional)

**Priority**: WAF Recommendation Agent is a key requirement and should be prioritized.
