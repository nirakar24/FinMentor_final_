"""
Pydantic v2 schemas for LLM-powered advice generation endpoint.
"""
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


class ActionStep(BaseModel):
    """Individual action step in financial advice"""
    
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed description")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level")


class AdviceGenerateRequest(BaseModel):
    """Request schema for POST /advice/generate"""
    
    user_id: str = Field(..., description="Unique user identifier")
    rules_output: Dict[str, Any] = Field(..., description="Full JSON from /evaluate endpoint")
    behavior_output: Dict[str, Any] = Field(..., description="Full JSON from /behavior/detect endpoint")
    persona_type: Literal["gig_worker", "salaried", "default"] = Field(
        default="default",
        description="User income persona type"
    )
    user_query: str | None = Field(
        default=None,
        description="User's specific financial question (e.g., 'Can I go on vacation?', 'Should I buy a new phone?')"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR_12345",
                    "rules_output": {
                        "risk_summary": {
                            "total_risk_score": 85,
                            "weighted_severity": "high",
                            "top_risks": [
                                {"id": "R-001", "dimension": "savings", "severity": "high"}
                            ]
                        }
                    },
                    "behavior_output": {
                        "user_id": "USR_12345",
                        "behavior_flags": ["unstable_cashflow", "high_discretionary_spender"],
                        "behavior_score": 60,
                        "risk_level": "medium"
                    },
                    "persona_type": "gig_worker",
                    "user_query": "Can I go on a vacation?"
                }
            ]
        }
    }


class AdviceGenerateResponse(BaseModel):
    """Response schema for POST /advice/generate (LLM output)"""
    
    user_id: str = Field(..., description="User identifier")
    summary: str = Field(..., description="1-2 line financial health summary")
    top_risks: List[str] = Field(default_factory=list, description="Top identified risks")
    behavioral_warnings: List[str] = Field(default_factory=list, description="Behavioral warnings")
    action_steps: List[ActionStep] = Field(default_factory=list, description="Actionable steps")
    savings_tip: str = Field(..., description="Savings advice")
    spending_tip: str = Field(..., description="Spending advice")
    stability_tip: str = Field(..., description="Cashflow stability advice")
    confidence_message: str = Field(..., description="Confidence/encouragement message")
    generated_at: str = Field(..., description="ISO 8601 timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR_12345",
                    "summary": "Your cashflow is unstable with high discretionary spending. Immediate action needed.",
                    "top_risks": [
                        "Insufficient emergency fund",
                        "High spending volatility",
                        "Low savings rate"
                    ],
                    "behavioral_warnings": [
                        "Discretionary spending exceeds 30% threshold",
                        "Cashflow stability below 60%"
                    ],
                    "action_steps": [
                        {
                            "title": "Build 3-month emergency buffer",
                            "description": "Save ₹15,000 per month to reach ₹45,000 safety net",
                            "priority": "high"
                        }
                    ],
                    "savings_tip": "Automate 20% of variable income into a separate account immediately upon receipt",
                    "spending_tip": "Cut discretionary expenses by 15% - focus on subscription audits",
                    "stability_tip": "Track daily expenses to identify patterns during high-income periods",
                    "confidence_message": "Small consistent actions compound. You can stabilize your finances in 90 days.",
                    "generated_at": "2025-11-29T12:34:56.789Z"
                }
            ]
        }
    }
