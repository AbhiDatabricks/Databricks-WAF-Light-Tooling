"""
Data models for WAF Assessment Tool
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Pillar(str, Enum):
    """WAF Pillar enumeration"""
    RELIABILITY = "reliability"
    GOVERNANCE = "governance"
    COST = "cost"
    PERFORMANCE = "performance"


class MetricStatus(str, Enum):
    """Metric implementation status"""
    PASS = "Pass"
    FAIL = "Fail"
    MET = "Met"
    NOT_MET = "Not Met"


class Metric(BaseModel):
    """Individual WAF control metric"""
    waf_id: str = Field(..., description="WAF identifier (e.g., R-01-01)")
    principle: str = Field(..., description="WAF principle")
    best_practice: Optional[str] = Field(None, description="Best practice description")
    description: Optional[str] = Field(None, description="Metric description")
    score_percentage: float = Field(..., description="Current score percentage")
    threshold_percentage: float = Field(..., description="Threshold percentage")
    threshold_met: bool = Field(..., description="Whether threshold is met")
    implemented: str = Field(..., description="Implementation status (Pass/Fail)")
    current_percentage: Optional[float] = Field(None, description="Current percentage value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "waf_id": "R-01-01",
                "principle": "Design for failure",
                "best_practice": "Use Delta Lake format",
                "score_percentage": 85.5,
                "threshold_percentage": 80.0,
                "threshold_met": True,
                "implemented": "Pass"
            }
        }


class PrincipleScore(BaseModel):
    """Principle-level completion score"""
    principle: str = Field(..., description="WAF principle name")
    completion_percent: float = Field(..., description="Completion percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "principle": "Design for failure",
                "completion_percent": 75.0
            }
        }


class PillarScore(BaseModel):
    """Pillar-level assessment score"""
    pillar: str = Field(..., description="Pillar name")
    completion_percent: float = Field(..., description="Overall completion percentage")
    metrics: List[Metric] = Field(default_factory=list, description="Individual metrics")
    principles: List[PrincipleScore] = Field(default_factory=list, description="Principle-level scores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pillar": "reliability",
                "completion_percent": 38.0,
                "metrics": [],
                "principles": []
            }
        }


class WAFScores(BaseModel):
    """Complete WAF assessment scores"""
    reliability: PillarScore
    governance: PillarScore
    cost: PillarScore
    performance: PillarScore
    summary: Dict[str, float] = Field(default_factory=dict, description="Summary scores")
    timestamp: datetime = Field(default_factory=datetime.now, description="Assessment timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reliability": {
                    "pillar": "reliability",
                    "completion_percent": 38.0
                },
                "governance": {
                    "pillar": "governance",
                    "completion_percent": 65.0
                },
                "cost": {
                    "pillar": "cost",
                    "completion_percent": 45.0
                },
                "performance": {
                    "pillar": "performance",
                    "completion_percent": 72.0
                }
            }
        }


class Recommendation(BaseModel):
    """Actionable recommendation for improving WAF scores"""
    waf_id: str = Field(..., description="WAF identifier")
    pillar: str = Field(..., description="Pillar name")
    issue: str = Field(..., description="Issue description")
    recommendation: str = Field(..., description="Recommendation text")
    action_items: List[str] = Field(default_factory=list, description="Action items")
    code_example: Optional[str] = Field(None, description="Code example")
    priority: int = Field(default=3, description="Priority (1=high, 3=low)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "waf_id": "R-01-03",
                "pillar": "reliability",
                "issue": "DLT usage is only 25% (threshold: 30%)",
                "recommendation": "Increase DLT usage to 30% or more",
                "action_items": [
                    "Migrate existing pipelines to DLT",
                    "Use DLT for new data quality checks"
                ],
                "priority": 1
            }
        }
