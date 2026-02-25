"""
WAF Assessment Tool - Core Query Library

This module provides reusable query functions that extract SQL logic
from the dashboard into Python functions for use by REST API, MCP, and Agent services.
"""

# Use relative imports (standard Python package pattern)
from .databricks_client import DatabricksClient
from .models import (
    PillarScore,
    Metric,
    PrincipleScore,
    WAFScores,
    Recommendation
)
from .queries import (
    get_reliability_scores,
    get_governance_scores,
    get_cost_scores,
    get_performance_scores,
    get_all_scores,
    get_summary_scores,
    get_metric_by_id
)

__version__ = "1.0.0"
__all__ = [
    "DatabricksClient",
    "PillarScore",
    "Metric",
    "PrincipleScore",
    "WAFScores",
    "Recommendation",
    "get_reliability_scores",
    "get_governance_scores",
    "get_cost_scores",
    "get_performance_scores",
    "get_all_scores",
    "get_summary_scores",
    "get_metric_by_id",
]
