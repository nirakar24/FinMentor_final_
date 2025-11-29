"""
Pydantic v2 schemas for behavior detection endpoint.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class BehaviorDetectRequest(BaseModel):
    """Request schema for POST /behavior/detect"""
    
    user_id: str = Field(..., description="Unique user identifier")
    avg_daily_expense: float = Field(..., ge=0, description="Average daily expense")
    high_spend_days: int = Field(..., ge=0, description="Number of high spend days")
    cashflow_stability: float = Field(..., ge=0.0, le=1.0, description="Cashflow stability score (0-1)")
    discretionary_ratio: float = Field(..., ge=0.0, le=1.0, description="Discretionary spending ratio (0-1)")
    zero_income_days: Optional[int] = Field(default=0, ge=0, description="Days with zero income")
    consecutive_deficit_count: Optional[int] = Field(default=0, ge=0, description="Consecutive deficit count")
    large_transactions: Optional[List[float]] = Field(default_factory=list, description="List of large transaction amounts")
    cash_withdrawals: Optional[List[float]] = Field(default_factory=list, description="List of cash withdrawal amounts")

    @field_validator("large_transactions", "cash_withdrawals", mode="before")
    @classmethod
    def ensure_list(cls, v):
        """Ensure optional arrays default to empty list if None"""
        if v is None:
            return []
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR_12345",
                    "avg_daily_expense": 450.0,
                    "high_spend_days": 8,
                    "cashflow_stability": 0.45,
                    "discretionary_ratio": 0.42,
                    "zero_income_days": 6,
                    "consecutive_deficit_count": 3,
                    "large_transactions": [2500.0, 3200.0],
                    "cash_withdrawals": [5000.0, 3000.0]
                }
            ]
        }
    }


class BehaviorDetectResponse(BaseModel):
    """Response schema for POST /behavior/detect"""
    
    user_id: str = Field(..., description="User identifier")
    behavior_flags: List[str] = Field(default_factory=list, description="Detected behavioral flags")
    behavior_score: int = Field(..., ge=0, le=100, description="Behavior risk score (0-100)")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Risk classification")
    generated_at: str = Field(..., description="ISO 8601 timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR_12345",
                    "behavior_flags": [
                        "high_discretionary_spender",
                        "frequent_high_spend_days",
                        "unstable_cashflow",
                        "income_gap_risk",
                        "recurring_deficit",
                        "spike_transaction_behavior"
                    ],
                    "behavior_score": 100,
                    "risk_level": "high",
                    "generated_at": "2025-11-29T12:34:56.789Z"
                }
            ]
        }
    }
