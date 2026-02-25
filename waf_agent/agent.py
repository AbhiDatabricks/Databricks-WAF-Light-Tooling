"""
WAF Recommendation Agent

Uses Databricks Foundation Model APIs (Claude) and Vector Search to provide
intelligent recommendations based on WAF scores.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient

from waf_core.databricks_client import DatabricksClient
from waf_core.queries import get_all_scores, get_metric_by_id

logger = logging.getLogger(__name__)


class WAFRecommendationAgent:
    """AI agent that provides WAF recommendations using Claude"""
    
    def __init__(
        self,
        workspace_client: Optional[WorkspaceClient] = None,
        warehouse_id: Optional[str] = None
    ):
        """
        Initialize the WAF Recommendation Agent
        
        Args:
            workspace_client: Databricks WorkspaceClient (uses default if None)
            warehouse_id: SQL Warehouse ID (required for querying scores)
        """
        self.w = workspace_client or WorkspaceClient()
        self.warehouse_id = warehouse_id or os.getenv("DATABRICKS_WAREHOUSE_ID", "")
        
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required")
        
        self.waf_client = DatabricksClient(
            workspace_client=self.w,
            warehouse_id=self.warehouse_id
        )
        
        # Claude model endpoint (Databricks Foundation Model API)
        self.model_name = os.getenv("DATABRICKS_FOUNDATION_MODEL", "databricks-meta-llama-3-1-70b-instruct")
        self.endpoint_name = os.getenv("DATABRICKS_ENDPOINT_NAME", None)
    
    def get_waf_context(self) -> Dict[str, Any]:
        """Get current WAF scores and failing metrics as context"""
        try:
            scores = get_all_scores(self.waf_client, include_metrics=True, include_principles=True)
            
            # Calculate overall score
            overall_score = (
                scores.reliability.completion_percent +
                scores.governance.completion_percent +
                scores.cost.completion_percent +
                scores.performance.completion_percent
            ) / 4.0
            
            # Get failing metrics
            failing_metrics = []
            for pillar_score in [scores.reliability, scores.governance, scores.cost, scores.performance]:
                for metric in pillar_score.metrics:
                    if not metric.threshold_met or metric.implemented == "Fail":
                        failing_metrics.append({
                            "waf_id": metric.waf_id,
                            "pillar": pillar_score.pillar,
                            "principle": metric.principle,
                            "best_practice": metric.best_practice or metric.description,
                            "current_score": metric.score_percentage,
                            "threshold": metric.threshold_percentage,
                            "gap": metric.threshold_percentage - metric.score_percentage
                        })
            
            # Sort by gap (largest gaps first)
            failing_metrics.sort(key=lambda x: x["gap"], reverse=True)
            
            return {
                "overall_score": overall_score,
                "pillar_scores": {
                    "reliability": scores.reliability.completion_percent,
                    "governance": scores.governance.completion_percent,
                    "cost": scores.cost.completion_percent,
                    "performance": scores.performance.completion_percent
                },
                "failing_metrics": failing_metrics[:10],  # Top 10 failing metrics
                "total_failing": len(failing_metrics)
            }
        except Exception as e:
            logger.error(f"Error getting WAF context: {e}", exc_info=True)
            return {"error": str(e)}
    
    def search_documentation(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search Databricks documentation using Vector Search
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant documentation snippets
        """
        try:
            # Use Databricks Vector Search (if configured)
            # For now, return empty list - Vector Search setup is workspace-specific
            # TODO: Configure Vector Search endpoint and index
            
            # Fallback: Return general Databricks documentation links
            return [
                {
                    "title": "Databricks Documentation",
                    "url": "https://docs.databricks.com",
                    "snippet": "General Databricks documentation and best practices"
                }
            ]
        except Exception as e:
            logger.warning(f"Vector Search not available: {e}")
            return []
    
    def generate_recommendation(
        self,
        user_question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate recommendation using Claude via Databricks Foundation Model API
        
        Args:
            user_question: User's question about WAF scores
            conversation_history: Previous conversation messages
            
        Returns:
            Agent's response with recommendations
        """
        try:
            # Get current WAF context
            waf_context = self.get_waf_context()
            
            if "error" in waf_context:
                return f"I encountered an error retrieving WAF scores: {waf_context['error']}"
            
            # Build system prompt
            system_prompt = """You are a Databricks Well-Architected Framework (WAF) expert assistant. 
Your role is to:
1. Analyze WAF assessment scores and identify issues
2. Provide actionable recommendations to improve scores
3. Answer questions about WAF principles and best practices
4. Help users understand why their scores are low and how to improve them

Be concise, practical, and provide specific, actionable advice with code examples when relevant."""

            # Build user prompt with context
            context_str = json.dumps(waf_context, indent=2)
            user_prompt = f"""Current WAF Assessment Context:
{context_str}

User Question: {user_question}

Please provide a helpful response based on the WAF scores above. If the user is asking about specific metrics or pillars, reference the actual scores and provide concrete recommendations."""

            # Build messages for chat completion
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages = [{"role": "system", "content": system_prompt}] + conversation_history + [{"role": "user", "content": user_prompt}]
            
            # Call Databricks Foundation Model API (Claude)
            # Use the serving endpoint or model serving
            try:
                # Try to use Foundation Model serving endpoint
                if self.endpoint_name:
                    # Use endpoint-based serving
                    response = self.w.serving_endpoints.query(
                        name=self.endpoint_name,
                        dataframe_records=[{"messages": messages}]
                    )
                    result = response.predictions[0] if response.predictions else None
                else:
                    # Use Foundation Model API directly
                    # Note: This requires proper endpoint configuration
                    # For now, return a structured response
                    result = self._call_claude_direct(messages)
                
                if result:
                    return result
                else:
                    return "I'm having trouble connecting to the AI model. Please check your Databricks Foundation Model API configuration."
            
            except Exception as e:
                logger.error(f"Error calling Foundation Model API: {e}", exc_info=True)
                # Fallback: Generate response based on context
                return self._generate_fallback_response(user_question, waf_context)
        
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}", exc_info=True)
            return f"I encountered an error: {str(e)}"
    
    def _call_claude_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call Claude via Databricks Foundation Model API"""
        try:
            # Use Databricks Foundation Model API
            # Format: Use Foundation Model serving endpoint or direct API call
            workspace_url = self.w.config.host
            token = getattr(self.w.config, 'token', None) or getattr(self.w.config, '_token', None)
            
            if not token:
                logger.warning("No token available for Foundation Model API")
                return None
            
            # Build request payload for chat completion (Claude format)
            # Extract system message and user messages
            system_content = None
            chat_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    chat_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Build payload for Foundation Model API
            payload = {
                "messages": chat_messages,
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            if system_content:
                payload["system"] = system_content
            
            # Try serving endpoint first (if configured)
            if self.endpoint_name:
                try:
                    response = self.w.serving_endpoints.query(
                        name=self.endpoint_name,
                        dataframe_records=[payload]
                    )
                    if response.predictions:
                        pred = response.predictions[0]
                        # Handle different response formats
                        if isinstance(pred, dict):
                            if "choices" in pred:
                                return pred["choices"][0].get("message", {}).get("content", "")
                            elif "candidates" in pred:
                                return pred["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            elif "text" in pred:
                                return pred["text"]
                        return str(pred)
                except Exception as e:
                    logger.warning(f"Serving endpoint failed: {e}, trying direct API")
            
            # Fallback: Use Foundation Model API directly via REST
            # Use the model name (e.g., "databricks-meta-llama-3-1-70b-instruct" or "anthropic-claude-3-5-sonnet")
            model_name = self.endpoint_name or self.model_name or "databricks-meta-llama-3-1-70b-instruct"
            
            import requests
            api_url = f"{workspace_url}/api/2.0/serving-endpoints/{model_name}/invocations"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                api_url,
                headers=headers,
                json={"dataframe_records": [payload]},
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("predictions"):
                    pred = result["predictions"][0]
                    if isinstance(pred, dict):
                        if "choices" in pred:
                            return pred["choices"][0].get("message", {}).get("content", "")
                        elif "candidates" in pred:
                            return pred["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        elif "text" in pred:
                            return pred["text"]
                    return str(pred)
            else:
                logger.warning(f"Foundation Model API returned {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}", exc_info=True)
            return None
    
    def _generate_fallback_response(self, question: str, context: Dict[str, Any]) -> str:
        """Generate a response without AI model (fallback)"""
        question_lower = question.lower()
        
        if "overall" in question_lower or "score" in question_lower:
            overall = context.get("overall_score", 0)
            return f"Your overall WAF score is {overall:.1f}%. "
        
        if "reliability" in question_lower:
            score = context.get("pillar_scores", {}).get("reliability", 0)
            failing = [m for m in context.get("failing_metrics", []) if m.get("pillar") == "reliability"]
            response = f"Your Reliability score is {score:.1f}%."
            if failing:
                response += f" Key issues: {', '.join([m['waf_id'] for m in failing[:3]])}"
            return response
        
        if "governance" in question_lower:
            score = context.get("pillar_scores", {}).get("governance", 0)
            return f"Your Governance score is {score:.1f}%."
        
        if "cost" in question_lower:
            score = context.get("pillar_scores", {}).get("cost", 0)
            return f"Your Cost Optimization score is {score:.1f}%."
        
        if "performance" in question_lower:
            score = context.get("pillar_scores", {}).get("performance", 0)
            return f"Your Performance Efficiency score is {score:.1f}%."
        
        # Generic response
        failing_count = context.get("total_failing", 0)
        return f"Based on your WAF assessment, you have {failing_count} failing metrics. " \
               f"Your overall score is {context.get('overall_score', 0):.1f}%. " \
               f"Would you like specific recommendations for any pillar?"


def create_agent(
    workspace_client: Optional[WorkspaceClient] = None,
    warehouse_id: Optional[str] = None
) -> WAFRecommendationAgent:
    """Factory function to create a WAF Recommendation Agent"""
    return WAFRecommendationAgent(
        workspace_client=workspace_client,
        warehouse_id=warehouse_id
    )
