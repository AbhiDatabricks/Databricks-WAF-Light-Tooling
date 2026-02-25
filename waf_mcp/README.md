# WAF Assessment Tool - MCP Service

MCP (Model Context Protocol) service that exposes WAF scores and metrics as tools for AI assistants.

## Overview

This MCP server provides tools that AI assistants (Claude Desktop, Cursor, GitHub Copilot, etc.) can use to query WAF assessment scores and get recommendations.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export DATABRICKS_WAREHOUSE_ID="your-warehouse-id"
```

Or configure in your MCP client settings.

## Running the MCP Server

```bash
python -m waf_mcp.server
```

Or integrate with your MCP client configuration.

## Available Tools

### 1. `get_waf_scores`
Get overall WAF assessment scores for all pillars.

**Input:** None

**Output:** JSON with reliability, governance, cost, and performance scores.

### 2. `get_pillar_score`
Get detailed score for a specific WAF pillar.

**Input:**
- `pillar` (required): One of: "reliability", "governance", "cost", "performance"

**Output:** JSON with pillar score, metrics, and principles.

### 3. `get_failing_metrics`
Get all WAF control metrics that are failing (below threshold).

**Input:**
- `pillar` (optional): Filter by pillar, or "all" for all pillars

**Output:** JSON with list of failing metrics and count.

### 4. `get_metric_details`
Get detailed information about a specific WAF control metric.

**Input:**
- `waf_id` (required): The WAF control ID (e.g., "R-01-01", "G-02-03")

**Output:** JSON with metric details.

### 5. `get_recommendations`
Get actionable recommendations to improve WAF scores.

**Input:**
- `pillar` (optional): Filter by pillar, or "all" for all pillars
- `priority` (optional): Filter by priority ("high", "medium", "low", "all")

**Output:** JSON with recommendations sorted by priority.

## Integration Examples

### Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "waf-assessment": {
      "command": "python",
      "args": ["-m", "waf_mcp.server"],
      "env": {
        "DATABRICKS_WAREHOUSE_ID": "your-warehouse-id"
      }
    }
  }
}
```

### Cursor

Configure in Cursor's MCP settings to enable WAF queries in your AI assistant.

## Use Cases

- Ask AI assistants: "What's my WAF score?"
- Natural language queries: "Show me all governance metrics that are failing"
- Get recommendations: "What should I do to improve my reliability score?"
