"""
WAF Assessment Query Execution Functions

This module provides functions to execute WAF assessment queries
and return structured Python objects.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from .databricks_client import DatabricksClient
from .models import (
    PillarScore,
    Metric,
    PrincipleScore,
    WAFScores,
    Pillar
)

logger = logging.getLogger(__name__)

# Load queries from extracted JSON
_QUERIES_CACHE: Optional[Dict[str, Any]] = None

def _load_queries() -> Dict[str, Any]:
    """Load queries from extracted JSON file"""
    global _QUERIES_CACHE
    if _QUERIES_CACHE is None:
        # Try multiple possible locations
        possible_paths = [
            # In workspace deployment
            Path(__file__).parent.parent / "extracted_queries.json",
            # In development
            Path(__file__).parent.parent / "DONOTCHECKIN" / "utils" / "docs" / "query_analysis" / "extracted_queries.json",
            # Absolute path fallback
            Path("/Workspace") / "extracted_queries.json",
        ]
        
        queries_file = None
        for path in possible_paths:
            if path.exists():
                queries_file = path
                break
        
        if queries_file:
            with open(queries_file, 'r') as f:
                _QUERIES_CACHE = json.load(f)
            logger.info(f"Loaded queries from: {queries_file}")
        else:
            logger.warning(f"Queries file not found in any of: {possible_paths}")
            _QUERIES_CACHE = {}
    return _QUERIES_CACHE

def _get_query(pillar: str, query_type: str) -> str:
    """Get SQL query for a specific pillar and query type"""
    queries = _load_queries()
    query_data = queries.get(pillar, {}).get(query_type, {})
    if isinstance(query_data, dict):
        return query_data.get("query", "")
    return ""

def _execute_query(client: DatabricksClient, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a query and return results"""
    try:
        # Use SDK method which works with both SP and PAT authentication
        # Replace parameters in query if provided
        if parameters:
            for key, value in parameters.items():
                # Simple parameter replacement (for :param_name format)
                query = query.replace(f":{key}", str(value))
        
        return client.execute_query_sdk(query)
    except ValueError as e:
        # Configuration errors (e.g., missing warehouse_id)
        logger.error(f"Configuration error in query execution: {str(e)}")
        raise
    except PermissionError as e:
        # Permission errors
        logger.error(f"Permission error in query execution: {str(e)}")
        raise
    except TimeoutError as e:
        # Timeout errors
        logger.error(f"Timeout error in query execution: {str(e)}")
        raise
    except Exception as e:
        # Other errors
        logger.error(f"Error executing query: {str(e)}")
        logger.debug(f"Query that failed: {query[:200]}...")  # Log first 200 chars of query
        raise

def get_reliability_scores(
    client: DatabricksClient,
    include_metrics: bool = True,
    include_principles: bool = True
) -> PillarScore:
    """
    Get Reliability pillar scores
    
    Args:
        client: Databricks client instance
        include_metrics: Whether to include individual metrics
        include_principles: Whether to include principle-level scores
        
    Returns:
        PillarScore object with Reliability assessment
    """
    logger.info("Fetching Reliability scores...")
    
    # Get total percentage
    total_query = _get_query("reliability", "total_percentage")
    total_results = _execute_query(client, total_query)
    completion_percent = total_results[0].get("completion_percent", 0.0) if total_results else 0.0
    
    metrics = []
    if include_metrics:
        controls_query = _get_query("reliability", "waf_controls")
        controls_results = _execute_query(client, controls_query)
        metrics = [
            Metric(
                waf_id=row.get("waf_id", ""),
                principle=row.get("principle", ""),
                best_practice=row.get("best_practice"),
                score_percentage=float(row.get("score_percentage", 0.0)),
                threshold_percentage=float(row.get("threshold_percentage", 0.0)),
                threshold_met=row.get("threshold_met") == "Met",
                implemented=row.get("implemented", "Fail"),
                current_percentage=float(row.get("score_percentage", 0.0))
            )
            for row in controls_results
        ]
    
    principles = []
    if include_principles:
        principles_query = _get_query("reliability", "waf_principal_percentage")
        principles_results = _execute_query(client, principles_query)
        principles = [
            PrincipleScore(
                principle=row.get("principle", ""),
                completion_percent=float(row.get("completion_percent", 0.0))
            )
            for row in principles_results
        ]
    
    return PillarScore(
        pillar="reliability",
        completion_percent=float(completion_percent),
        metrics=metrics,
        principles=principles
    )

def get_governance_scores(
    client: DatabricksClient,
    include_metrics: bool = True,
    include_principles: bool = True
) -> PillarScore:
    """Get Governance pillar scores"""
    logger.info("Fetching Governance scores...")
    
    total_query = _get_query("governance", "total_percentage")
    total_results = _execute_query(client, total_query)
    completion_percent = total_results[0].get("completion_percent", 0.0) if total_results else 0.0
    
    metrics = []
    if include_metrics:
        controls_query = _get_query("governance", "waf_controls")
        controls_results = _execute_query(client, controls_query)
        metrics = [
            Metric(
                waf_id=row.get("waf_id", ""),
                principle=row.get("principle", ""),
                description=row.get("description"),
                score_percentage=float(row.get("score_percentage", 0.0)),
                threshold_percentage=float(row.get("threshold_percentage", 0.0)),
                threshold_met=row.get("threshold_met") == "Met",
                implemented=row.get("implemented", "Fail"),
                current_percentage=float(row.get("score_percentage", 0.0))
            )
            for row in controls_results
        ]
    
    principles = []
    if include_principles:
        principles_query = _get_query("governance", "waf_principal_percentage")
        principles_results = _execute_query(client, principles_query)
        principles = [
            PrincipleScore(
                principle=row.get("principle", ""),
                completion_percent=float(row.get("completion_percent", 0.0))
            )
            for row in principles_results
        ]
    
    return PillarScore(
        pillar="governance",
        completion_percent=float(completion_percent),
        metrics=metrics,
        principles=principles
    )

def get_cost_scores(
    client: DatabricksClient,
    include_metrics: bool = True,
    include_principles: bool = True
) -> PillarScore:
    """Get Cost Optimization pillar scores"""
    logger.info("Fetching Cost Optimization scores...")
    
    total_query = _get_query("cost", "total_percentage")
    total_results = _execute_query(client, total_query)
    completion_percent = total_results[0].get("completion_percent", 0.0) if total_results else 0.0
    
    metrics = []
    if include_metrics:
        controls_query = _get_query("cost", "waf_controls")
        controls_results = _execute_query(client, controls_query)
        metrics = [
            Metric(
                waf_id=row.get("waf_id", ""),
                principle=row.get("principle", ""),
                best_practice=row.get("best_practice"),
                score_percentage=float(row.get("score_percentage", 0.0)),
                threshold_percentage=float(row.get("threshold_percentage", 0.0)),
                threshold_met=row.get("threshold_met") == "Met",
                implemented=row.get("implemented", "Fail"),
                current_percentage=float(row.get("score_percentage", 0.0))
            )
            for row in controls_results
        ]
    
    principles = []
    if include_principles:
        principles_query = _get_query("cost", "waf_principal_percentage")
        principles_results = _execute_query(client, principles_query)
        principles = [
            PrincipleScore(
                principle=row.get("principle", ""),
                completion_percent=float(row.get("completion_percent", 0.0))
            )
            for row in principles_results
        ]
    
    return PillarScore(
        pillar="cost",
        completion_percent=float(completion_percent),
        metrics=metrics,
        principles=principles
    )

def get_performance_scores(
    client: DatabricksClient,
    include_metrics: bool = True,
    include_principles: bool = True
) -> PillarScore:
    """Get Performance Efficiency pillar scores"""
    logger.info("Fetching Performance Efficiency scores...")
    
    total_query = _get_query("performance", "total_percentage")
    total_results = _execute_query(client, total_query)
    completion_percent = total_results[0].get("completion_percent", 0.0) if total_results else 0.0
    
    metrics = []
    if include_metrics:
        controls_query = _get_query("performance", "waf_controls")
        controls_results = _execute_query(client, controls_query)
        metrics = [
            Metric(
                waf_id=row.get("waf_id", ""),
                principle=row.get("principle", ""),
                best_practice=row.get("best_practice"),
                score_percentage=float(row.get("score_percentage", 0.0)),
                threshold_percentage=float(row.get("threshold_percentage", 0.0)),
                threshold_met=row.get("threshold_met") == "Met",
                implemented=row.get("implemented", "Fail"),
                current_percentage=float(row.get("score_percentage", 0.0))
            )
            for row in controls_results
        ]
    
    principles = []
    if include_principles:
        principles_query = _get_query("performance", "waf_principal_percentage")
        principles_results = _execute_query(client, principles_query)
        principles = [
            PrincipleScore(
                principle=row.get("principle", ""),
                completion_percent=float(row.get("completion_percent", 0.0))
            )
            for row in principles_results
        ]
    
    return PillarScore(
        pillar="performance",
        completion_percent=float(completion_percent),
        metrics=metrics,
        principles=principles
    )

def get_all_scores(
    client: DatabricksClient,
    include_metrics: bool = True,
    include_principles: bool = True
) -> WAFScores:
    """
    Get scores for all pillars
    
    Args:
        client: Databricks client instance
        include_metrics: Whether to include individual metrics
        include_principles: Whether to include principle-level scores
        
    Returns:
        WAFScores object with all pillar assessments
    """
    logger.info("Fetching all WAF scores...")
    
    reliability = get_reliability_scores(client, include_metrics, include_principles)
    governance = get_governance_scores(client, include_metrics, include_principles)
    cost = get_cost_scores(client, include_metrics, include_principles)
    performance = get_performance_scores(client, include_metrics, include_principles)
    
    # Get summary
    summary_query = _get_query("summary", "total_percentage_across_pillars")
    summary_results = _execute_query(client, summary_query)
    summary = {
        row.get("pillar", "").lower(): float(row.get("completion_percent", 0.0))
        for row in summary_results
    }
    
    return WAFScores(
        reliability=reliability,
        governance=governance,
        cost=cost,
        performance=performance,
        summary=summary
    )

def get_summary_scores(client: DatabricksClient) -> Dict[str, float]:
    """Get summary scores across all pillars"""
    summary_query = _get_query("summary", "total_percentage_across_pillars")
    summary_results = _execute_query(client, summary_query)
    return {
        row.get("pillar", "").lower(): float(row.get("completion_percent", 0.0))
        for row in summary_results
    }

def get_metric_by_id(
    client: DatabricksClient,
    waf_id: str
) -> Optional[Metric]:
    """
    Get a specific metric by WAF ID (e.g., 'R-01-01')
    
    Args:
        client: Databricks client instance
        waf_id: WAF identifier (e.g., 'R-01-01', 'G-02-03')
        
    Returns:
        Metric object if found, None otherwise
    """
    # Determine pillar from WAF ID prefix
    pillar_map = {
        "R": "reliability",
        "G": "governance",
        "C": "CO",  # Cost uses CO prefix
        "P": "PE",  # Performance uses PE prefix
    }
    
    prefix = waf_id[0] if waf_id else ""
    if prefix == "C" and waf_id.startswith("CO"):
        pillar = "cost"
    elif prefix == "P" and waf_id.startswith("PE"):
        pillar = "performance"
    else:
        pillar = pillar_map.get(prefix, "").lower()
    
    if not pillar:
        logger.warning(f"Unknown pillar for WAF ID: {waf_id}")
        return None
    
    # Get all metrics for the pillar
    if pillar == "reliability":
        pillar_score = get_reliability_scores(client, include_metrics=True, include_principles=False)
    elif pillar == "governance":
        pillar_score = get_governance_scores(client, include_metrics=True, include_principles=False)
    elif pillar == "cost":
        pillar_score = get_cost_scores(client, include_metrics=True, include_principles=False)
    elif pillar == "performance":
        pillar_score = get_performance_scores(client, include_metrics=True, include_principles=False)
    else:
        return None
    
    # Find the metric
    for metric in pillar_score.metrics:
        if metric.waf_id == waf_id:
            return metric
    
    return None
