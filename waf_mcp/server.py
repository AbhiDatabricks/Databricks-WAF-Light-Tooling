"""
MCP Server for WAF Assessment Tool

Exposes WAF scores and metrics as MCP tools for AI assistants.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from waf_core.databricks_client import DatabricksClient
from waf_core.queries import (
    get_all_scores,
    get_reliability_scores,
    get_governance_scores,
    get_cost_scores,
    get_performance_scores,
    get_metric_by_id
)

logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("waf-assessment-tool")

# Global client (will be initialized on first use)
_client: Optional[DatabricksClient] = None


def get_client() -> DatabricksClient:
    """Get or create Databricks client"""
    global _client
    if _client is None:
        import os
        from databricks.sdk import WorkspaceClient
        
        # Use Service Principal or user credentials
        workspace_client = WorkspaceClient()
        warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
        
        if not warehouse_id:
            raise ValueError("DATABRICKS_WAREHOUSE_ID environment variable not set")
        
        _client = DatabricksClient(
            workspace_client=workspace_client,
            warehouse_id=warehouse_id
        )
    
    return _client


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="get_waf_scores",
            description="Get overall WAF assessment scores for all pillars (Reliability, Governance, Cost, Performance)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_pillar_score",
            description="Get detailed score for a specific WAF pillar",
            inputSchema={
                "type": "object",
                "properties": {
                    "pillar": {
                        "type": "string",
                        "enum": ["reliability", "governance", "cost", "performance"],
                        "description": "The WAF pillar to get scores for"
                    }
                },
                "required": ["pillar"]
            }
        ),
        Tool(
            name="get_failing_metrics",
            description="Get all WAF control metrics that are failing (below threshold)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pillar": {
                        "type": "string",
                        "enum": ["reliability", "governance", "cost", "performance", "all"],
                        "description": "Filter by pillar, or 'all' for all pillars",
                        "default": "all"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_metric_details",
            description="Get detailed information about a specific WAF control metric",
            inputSchema={
                "type": "object",
                "properties": {
                    "waf_id": {
                        "type": "string",
                        "description": "The WAF control ID (e.g., 'R-01-01', 'G-02-03')"
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
                        "enum": ["reliability", "governance", "cost", "performance", "all"],
                        "description": "Filter recommendations by pillar, or 'all' for all pillars",
                        "default": "all"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low", "all"],
                        "description": "Filter by priority level",
                        "default": "all"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        client = get_client()
        
        if name == "get_waf_scores":
            scores = get_all_scores(client, include_metrics=False, include_principles=False)
            result = {
                "reliability": scores.reliability.completion_percent,
                "governance": scores.governance.completion_percent,
                "cost": scores.cost.completion_percent,
                "performance": scores.performance.completion_percent,
                "timestamp": scores.timestamp.isoformat()
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_pillar_score":
            pillar = arguments.get("pillar", "").lower()
            if pillar == "reliability":
                pillar_score = get_reliability_scores(client)
            elif pillar == "governance":
                pillar_score = get_governance_scores(client)
            elif pillar == "cost":
                pillar_score = get_cost_scores(client)
            elif pillar == "performance":
                pillar_score = get_performance_scores(client)
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Invalid pillar '{pillar}'. Must be one of: reliability, governance, cost, performance"
                )]
            
            result = {
                "pillar": pillar_score.pillar,
                "completion_percent": pillar_score.completion_percent,
                "metrics": [m.dict() for m in pillar_score.metrics],
                "principles": [p.dict() for p in pillar_score.principles]
            }
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_failing_metrics":
            pillar_filter = arguments.get("pillar", "all").lower()
            scores = get_all_scores(client, include_metrics=True, include_principles=False)
            
            failing_metrics = []
            for pillar_score in [scores.reliability, scores.governance, scores.cost, scores.performance]:
                if pillar_filter != "all" and pillar_score.pillar != pillar_filter:
                    continue
                
                for metric in pillar_score.metrics:
                    if not metric.threshold_met or metric.implemented == "Fail":
                        failing_metrics.append({
                            "waf_id": metric.waf_id,
                            "pillar": pillar_score.pillar,
                            "principle": metric.principle,
                            "score_percentage": metric.score_percentage,
                            "threshold_percentage": metric.threshold_percentage,
                            "gap": metric.threshold_percentage - metric.score_percentage
                        })
            
            return [TextContent(
                type="text",
                text=json.dumps({"failing_metrics": failing_metrics, "count": len(failing_metrics)}, indent=2)
            )]
        
        elif name == "get_metric_details":
            waf_id = arguments.get("waf_id", "")
            metric = get_metric_by_id(client, waf_id)
            
            if not metric:
                return [TextContent(
                    type="text",
                    text=f"Error: Metric '{waf_id}' not found"
                )]
            
            return [TextContent(
                type="text",
                text=json.dumps(metric.dict(), indent=2)
            )]
        
        elif name == "get_recommendations":
            pillar_filter = arguments.get("pillar", "all").lower()
            priority_filter = arguments.get("priority", "all").lower()
            
            scores = get_all_scores(client, include_metrics=True, include_principles=False)
            
            recommendations = []
            for pillar_score in [scores.reliability, scores.governance, scores.cost, scores.performance]:
                if pillar_filter != "all" and pillar_score.pillar != pillar_filter:
                    continue
                
                for metric in pillar_score.metrics:
                    if not metric.threshold_met or metric.implemented == "Fail":
                        priority = 1 if metric.score_percentage < 50 else 2
                        priority_str = "high" if priority == 1 else "medium"
                        
                        if priority_filter != "all" and priority_str != priority_filter:
                            continue
                        
                        recommendations.append({
                            "waf_id": metric.waf_id,
                            "pillar": pillar_score.pillar,
                            "principle": metric.principle,
                            "issue": f"Current score {metric.score_percentage}% is below threshold {metric.threshold_percentage}%",
                            "recommendation": f"Improve {metric.waf_id}: {metric.principle} - {metric.best_practice or metric.description or 'N/A'}",
                            "priority": priority_str,
                            "gap": metric.threshold_percentage - metric.score_percentage
                        })
            
            # Sort by priority and gap
            recommendations.sort(key=lambda x: (x["priority"] == "high", -x["gap"]))
            
            return [TextContent(
                type="text",
                text=json.dumps({"recommendations": recommendations, "count": len(recommendations)}, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    
    except Exception as e:
        logger.error(f"Error in tool '{name}': {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.list_resources(),
            app.list_tools(),
            app.call_tool()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
