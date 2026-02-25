"""
WAF Assessment Tool - REST API Main Application
"""
import os
import logging
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

from databricks.sdk import WorkspaceClient
from waf_core.databricks_client import DatabricksClient
from waf_core.queries import (
    get_all_scores,
    get_reliability_scores,
    get_governance_scores,
    get_cost_scores,
    get_performance_scores,
    get_metric_by_id,
    get_summary_scores
)
from waf_core.models import WAFScores, PillarScore, Metric, Recommendation

# Configure logging FIRST (before any imports that might use it)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import agent (optional)
try:
    from waf_agent.agent import WAFRecommendationAgent, create_agent
    AGENT_AVAILABLE = True
except ImportError as e:
    # Fallback if agent not available
    WAFRecommendationAgent = None
    create_agent = None
    AGENT_AVAILABLE = False
    logger.warning(f"WAF Agent not available: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="WAF Assessment Tool API",
    description="REST API for programmatic access to WAF assessment scores and metrics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABRICKS_WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "")

# OBO (On-Behalf-Of) environment variables (set by Databricks Apps when OBO is enabled)
# Check for OBO token in environment variables
DATABRICKS_USER_TOKEN = os.getenv("DATABRICKS_USER_TOKEN") or os.getenv("DATABRICKS_ACCESS_TOKEN")


def get_client(request: Request, authorization: Optional[str] = Header(None)) -> DatabricksClient:
    """
    Create Databricks client, prioritizing user credentials over Service Principal.
    
    Priority order:
    1. OAuth token from browser (X-Forwarded-Access-Token) - Same as dashboard ✅
    2. PAT from Authorization header (Bearer token)
    3. Service Principal (fallback - needs permissions)
    
    This matches how the dashboard works - it uses your user credentials, not SP.
    """
    from databricks.sdk.core import Config
    
    # Debug: Log all headers on first request to see what's available
    if not hasattr(get_client, '_header_logged'):
        logger.info("=== Available Request Headers ===")
        for header, value in sorted(request.headers.items()):
            # Mask sensitive values
            if 'token' in header.lower() or 'auth' in header.lower():
                masked = f"{str(value)[:30]}..." if len(str(value)) > 30 else str(value)
                logger.info(f"  {header}: {masked}")
            else:
                logger.debug(f"  {header}: {value}")
        get_client._header_logged = True
    
    # Priority 1: OAuth token from browser (OBO - On-Behalf-Of)
    # With user authorization OBO enabled, Databricks Apps forwards OAuth tokens
    # Check environment variables first (OBO may set these)
    forwarded_token = DATABRICKS_USER_TOKEN
    
    # Then check all possible header names (case-insensitive)
    if not forwarded_token:
        for header_name in [
            "X-Forwarded-Access-Token",
            "x-forwarded-access-token", 
            "X-Databricks-Access-Token",
            "x-databricks-access-token",
            "X-Databricks-OAuth-Token",
            "x-databricks-oauth-token",
            "Authorization"  # Sometimes in standard Authorization header
        ]:
            token_value = request.headers.get(header_name)
            if token_value:
                # If Authorization header, extract Bearer token
                if header_name.lower() == "authorization" and token_value.startswith("Bearer "):
                    forwarded_token = token_value[7:]  # Remove "Bearer " prefix
                else:
                    forwarded_token = token_value
                logger.info(f"✅ Found OAuth token in header: {header_name}")
                break
    
    if forwarded_token:
        logger.info(f"✅ Found forwarded token (length: {len(forwarded_token)})")
        logger.info("Using OAuth token from browser (OBO enabled)")
        try:
            # Use token as PAT (OAuth tokens from Databricks Apps work as PATs)
            # The token from X-Forwarded-Access-Token is already a valid access token
            workspace_client = WorkspaceClient(config=Config(token=forwarded_token, host=os.getenv("DATABRICKS_HOST")))
            # Validate by getting current user
            test_user = workspace_client.current_user.me()
            logger.info(f"✅ Token validated for user: {test_user.user_name}")
            logger.info(f"✅ Using user credentials: {test_user.user_name}")
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            logger.error("Falling back to Service Principal")
            workspace_client = WorkspaceClient()
    
    # Priority 2: PAT from Authorization header
    elif authorization:
        auth_parts = authorization.split()
        if len(auth_parts) == 2 and auth_parts[0].lower() == "bearer":
            pat = auth_parts[1]
            logger.info("Using PAT from Authorization header")
            workspace_client = WorkspaceClient(config=Config(token=pat, auth_type="pat"))
        else:
            # Invalid authorization format, fall back to SP
            logger.warning("Invalid Authorization header format, falling back to Service Principal")
            workspace_client = WorkspaceClient()
    
    # Priority 3: Service Principal (fallback - needs permissions granted)
    else:
        logger.error("❌ No user token found in any header!")
        logger.error("   This means OBO token is NOT being forwarded by Databricks Apps")
        logger.error("   Check:")
        logger.error("   1. OBO is enabled in app settings (Edit > User authorization)")
        logger.error("   2. 'sql' scope is added")
        logger.error("   3. User has consented to scopes")
        logger.error("   4. App was restarted after OBO configuration")
        logger.warning("⚠️  Falling back to Service Principal (will fail without SP permissions)")
        workspace_client = WorkspaceClient()
    
    # Get warehouse ID (required for SQL queries)
    warehouse_id = DATABRICKS_WAREHOUSE_ID or os.getenv("DATABRICKS_WAREHOUSE_ID", "")
    if not warehouse_id:
        raise HTTPException(
            status_code=500,
            detail="DATABRICKS_WAREHOUSE_ID not configured. Set environment variable or configure in app."
        )
    
    try:
        # Create client using WorkspaceClient (may be user OAuth, PAT, or SP)
        client = DatabricksClient(
            workspace_client=workspace_client,
            warehouse_id=warehouse_id
        )
        # Log which auth method is being used
        if forwarded_token:
            logger.info("✅ DatabricksClient created with user token (OBO)")
        elif authorization:
            logger.info("✅ DatabricksClient created with PAT")
        else:
            logger.warning("⚠️  DatabricksClient created with Service Principal")
        return client
    except Exception as e:
        logger.error(f"Error creating Databricks client: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Databricks client: {str(e)}")


# Response Models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ScoresResponse(BaseModel):
    reliability: float
    governance: float
    cost: float
    performance: float
    timestamp: datetime


class PillarScoresResponse(BaseModel):
    pillar: str
    completion_percent: float
    metrics: list
    principles: list
    timestamp: datetime


class MetricsResponse(BaseModel):
    metrics: list
    total_count: int
    timestamp: datetime


class MetricDetailResponse(BaseModel):
    metric: Optional[dict]
    timestamp: datetime


class RecommendationsResponse(BaseModel):
    recommendations: list
    total_count: int
    timestamp: datetime


class ContextResponse(BaseModel):
    workspace_id: Optional[str]
    assessment_timestamp: datetime
    overall_score: float
    pillars: dict
    priority_actions: list
    compliance_summary: dict


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    response: str
    timestamp: datetime


# API Endpoints

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint (no authentication required)"""
    # Health check doesn't need Databricks client, just return status
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )


@app.get("/api/v1/scores", response_model=ScoresResponse)
async def get_scores(client: DatabricksClient = Depends(get_client)):
    """Get overall WAF scores for all pillars"""
    try:
        scores = get_all_scores(client, include_metrics=False, include_principles=False)
        return ScoresResponse(
            reliability=scores.reliability.completion_percent,
            governance=scores.governance.completion_percent,
            cost=scores.cost.completion_percent,
            performance=scores.performance.completion_percent,
            timestamp=scores.timestamp
        )
    except ValueError as e:
        logger.error(f"Configuration error getting scores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except PermissionError as e:
        logger.error(f"Permission error getting scores: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting scores: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get scores: {str(e)}")


@app.get("/api/v1/scores/{pillar}", response_model=PillarScoresResponse)
async def get_pillar_score(
    pillar: str,
    client: DatabricksClient = Depends(get_client)
):
    """Get score for a specific pillar"""
    pillar = pillar.lower()
    
    try:
        if pillar == "reliability":
            pillar_score = get_reliability_scores(client)
        elif pillar == "governance":
            pillar_score = get_governance_scores(client)
        elif pillar == "cost":
            pillar_score = get_cost_scores(client)
        elif pillar == "performance":
            pillar_score = get_performance_scores(client)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid pillar: {pillar}")
        
        return PillarScoresResponse(
            pillar=pillar_score.pillar,
            completion_percent=pillar_score.completion_percent,
            metrics=[m.dict() for m in pillar_score.metrics],
            principles=[p.dict() for p in pillar_score.principles],
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error getting pillar score: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except PermissionError as e:
        logger.error(f"Permission error getting pillar score: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting pillar score: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get pillar score: {str(e)}")


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_all_metrics(client: DatabricksClient = Depends(get_client)):
    """Get all WAF control metrics"""
    try:
        scores = get_all_scores(client, include_metrics=True, include_principles=False)
        
        all_metrics = []
        for pillar_score in [scores.reliability, scores.governance, scores.cost, scores.performance]:
            all_metrics.extend([m.dict() for m in pillar_score.metrics])
        
        return MetricsResponse(
            metrics=all_metrics,
            total_count=len(all_metrics),
            timestamp=datetime.now()
        )
    except ValueError as e:
        logger.error(f"Configuration error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except PermissionError as e:
        logger.error(f"Permission error getting metrics: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.get("/api/v1/metrics/{waf_id}", response_model=MetricDetailResponse)
async def get_metric_details(
    waf_id: str,
    client: DatabricksClient = Depends(get_client)
):
    """Get details for a specific metric (e.g., R-01-01)"""
    try:
        metric = get_metric_by_id(client, waf_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric {waf_id} not found")
        
        return MetricDetailResponse(
            metric=metric.dict(),
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric details: {str(e)}")


@app.get("/api/v1/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    pillar: Optional[str] = None,
    client: DatabricksClient = Depends(get_client)
):
    """Get actionable recommendations to improve WAF scores"""
    try:
        scores = get_all_scores(client, include_metrics=True, include_principles=False)
        
        recommendations = []
        
        # Get failing metrics and generate recommendations
        for pillar_score in [scores.reliability, scores.governance, scores.cost, scores.performance]:
            if pillar and pillar.lower() != pillar_score.pillar:
                continue
            
            for metric in pillar_score.metrics:
                if not metric.threshold_met or metric.implemented == "Fail":
                    rec = Recommendation(
                        waf_id=metric.waf_id,
                        pillar=pillar_score.pillar,
                        issue=f"Current score {metric.score_percentage}% is below threshold {metric.threshold_percentage}%",
                        recommendation=f"Improve {metric.waf_id}: {metric.principle} - {metric.best_practice or metric.description or 'N/A'}",
                        action_items=[
                            f"Review current implementation for {metric.waf_id}",
                            f"Take steps to increase score from {metric.score_percentage}% to {metric.threshold_percentage}%"
                        ],
                        priority=1 if metric.score_percentage < 50 else 2
                    )
                    recommendations.append(rec.dict())
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])
        
        return RecommendationsResponse(
            recommendations=recommendations,
            total_count=len(recommendations),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@app.get("/api/v1/context", response_model=ContextResponse)
async def get_context(client: DatabricksClient = Depends(get_client)):
    """Get structured context for AI agents (optimized for LLM consumption)"""
    try:
        scores = get_all_scores(client, include_metrics=True, include_principles=True)
        
        # Calculate overall score (average of all pillars)
        overall_score = (
            scores.reliability.completion_percent +
            scores.governance.completion_percent +
            scores.cost.completion_percent +
            scores.performance.completion_percent
        ) / 4.0
        
        # Build pillar details
        pillars = {}
        for pillar_score in [scores.reliability, scores.governance, scores.cost, scores.performance]:
            failing_metrics = [
                {
                    "waf_id": m.waf_id,
                    "principle": m.principle,
                    "best_practice": m.best_practice or m.description,
                    "current_score": m.score_percentage,
                    "threshold": m.threshold_percentage,
                    "gap": m.threshold_percentage - m.score_percentage,
                    "recommendation": f"Improve {m.waf_id} to meet threshold of {m.threshold_percentage}%"
                }
                for m in pillar_score.metrics
                if not m.threshold_met
            ]
            
            status = "excellent" if pillar_score.completion_percent >= 80 else \
                     "good" if pillar_score.completion_percent >= 60 else \
                     "needs_improvement"
            
            pillars[pillar_score.pillar] = {
                "score": pillar_score.completion_percent,
                "status": status,
                "failing_metrics": failing_metrics,
                "recommendations": [
                    f"Focus on improving {m['waf_id']}" for m in failing_metrics[:3]
                ]
            }
        
        # Priority actions (top 5 failing metrics)
        all_failing = []
        for pillar_name, pillar_data in pillars.items():
            for metric in pillar_data["failing_metrics"]:
                all_failing.append({
                    **metric,
                    "pillar": pillar_name
                })
        
        priority_actions = sorted(all_failing, key=lambda x: x["gap"], reverse=True)[:5]
        
        # Compliance summary
        total_controls = sum(len(ps.metrics) for ps in [scores.reliability, scores.governance, scores.cost, scores.performance])
        passing_controls = sum(
            sum(1 for m in ps.metrics if m.threshold_met)
            for ps in [scores.reliability, scores.governance, scores.cost, scores.performance]
        )
        failing_controls = total_controls - passing_controls
        
        return ContextResponse(
            workspace_id=os.getenv("DATABRICKS_WORKSPACE_ID"),
            assessment_timestamp=datetime.now(),
            overall_score=overall_score,
            pillars=pillars,
            priority_actions=priority_actions,
            compliance_summary={
                "total_controls": total_controls,
                "passing_controls": passing_controls,
                "failing_controls": failing_controls,
                "compliance_percentage": round((passing_controls / total_controls * 100) if total_controls > 0 else 0, 2)
            }
        )
    except ValueError as e:
        logger.error(f"Configuration error getting context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except PermissionError as e:
        logger.error(f"Permission error getting context: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    client: DatabricksClient = Depends(get_client)
):
    """Chat with WAF Recommendation Agent"""
    if not AGENT_AVAILABLE or create_agent is None:
        raise HTTPException(
            status_code=503,
            detail="WAF Recommendation Agent is not available. The agent module failed to load."
        )
    try:
        # Create agent instance
        agent = create_agent(
            workspace_client=client.w,
            warehouse_id=client.warehouse_id
        )
        
        # Generate response
        response = agent.generate_recommendation(
            user_question=request.message,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now()
        )
    except ValueError as e:
        logger.error(f"Configuration error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except PermissionError as e:
        logger.error(f"Permission error in chat: {str(e)}")
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    # Use DATABRICKS_APP_PORT if available (for Databricks Apps), otherwise default to 8000
    port = int(os.environ.get("DATABRICKS_APP_PORT", "8000"))
    # Bind correctly and trust proxy headers (required for Databricks Apps)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
