# WAF Recommendation Agent

Conversational AI agent that understands WAF scores, retrieves context from Databricks documentation, and provides intelligent recommendations using Claude.

## Overview

The WAF Recommendation Agent:
- ✅ Uses **Databricks Foundation Model APIs** (Anthropic Claude) - **No API keys required!**
- ✅ Uses **Databricks Vector Search** for documentation retrieval - **No external vector stores!**
- ✅ Understands workspace-specific WAF scores
- ✅ Provides actionable recommendations with code examples

## Features

- **Context-Aware**: Retrieves current WAF scores and failing metrics
- **Intelligent Recommendations**: Uses Claude to generate personalized advice
- **Documentation Integration**: Can search Databricks docs for best practices
- **Conversational**: Maintains conversation history for follow-up questions

## Usage

### Via REST API

```python
import requests

response = requests.post(
    "https://waf-api-service-7474657119815190.aws.databricksapps.com/api/v1/chat",
    headers={"Authorization": "Bearer <token>"},
    json={
        "message": "Why is my reliability score low?",
        "conversation_history": []  # Optional
    }
)

print(response.json()["response"])
```

### Direct Python Usage

```python
from waf_agent.agent import create_agent
from databricks.sdk import WorkspaceClient

workspace_client = WorkspaceClient()
agent = create_agent(
    workspace_client=workspace_client,
    warehouse_id="your-warehouse-id"
)

response = agent.generate_recommendation(
    user_question="Why is my reliability score low?",
    conversation_history=None
)

print(response)
```

## Configuration

### Environment Variables

- `DATABRICKS_WAREHOUSE_ID`: SQL Warehouse ID (required)
- `DATABRICKS_FOUNDATION_MODEL`: Model name (default: "databricks-meta-llama-3-1-70b-instruct")
- `DATABRICKS_ENDPOINT_NAME`: Custom serving endpoint name (optional)

### Foundation Model Setup

1. **Use Default Foundation Model**: The agent will use Databricks-provided models (no setup needed)
2. **Use Custom Endpoint**: Configure a serving endpoint in your workspace and set `DATABRICKS_ENDPOINT_NAME`

## Example Conversations

```
User: "Why is my reliability score low?"
Agent: "Your reliability is 38% because:
- R-01-03: DLT usage is only 25% (threshold: 30%)
- R-01-05: Model Serving usage is 15% (threshold: 20%)

Would you like recommendations to improve these?"

User: "How do I increase DLT usage?"
Agent: [Retrieves Databricks docs on DLT]
       [Provides step-by-step guide with code examples]
       [Shows best practices]
```

## Integration

### Streamlit App

The agent can be integrated into the Streamlit app as a chat interface:

```python
from waf_agent.agent import create_agent

agent = create_agent(workspace_client, warehouse_id)

user_message = st.chat_input("Ask about your WAF scores...")
if user_message:
    response = agent.generate_recommendation(user_message)
    st.write(response)
```

## Architecture

```
User Question
    ↓
WAF Agent
    ↓
├─→ Get WAF Context (scores, failing metrics)
├─→ Search Documentation (Vector Search)
└─→ Generate Response (Claude API)
    ↓
Intelligent Recommendation
```
