from __future__ import annotations

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field


class BehaviorMetrics(BaseModel):
    avg_daily_expense: Optional[float] = None
    high_spend_days: Optional[int] = None
    cashflow_stability: Optional[float] = None
    discretionary_ratio: Optional[float] = None


class Forecast(BaseModel):
    predicted_income_next_month: Optional[float] = None
    predicted_expense_next_month: Optional[float] = None
    savings: Optional[float] = None
    confidence: Optional[float] = None


class Insights(BaseModel):
    top_spend_category: Optional[str] = None
    category_drift: Optional[str] = None


class NormalizedInput(BaseModel):
    user_id: str
    month: str
    avg_monthly_income: float
    avg_monthly_expense: float
    current_month_income: float
    current_month_expense: float
    savings_rate: Optional[float] = None
    income_volatility: Optional[float] = None
    risk_level: Optional[Literal["low", "moderate", "high"]] = None
    category_spend: Dict[str, float] = Field(default_factory=dict)
    behavior_metrics: Optional[BehaviorMetrics] = None
    forecast: Optional[Forecast] = None
    persona_type: Optional[str] = None
    confidence_score: Optional[float] = None
    last_updated: Optional[str] = None
    insights: Optional[Insights] = None

    # Derived
    net_cashflow: float
    expense_delta_pct: Optional[float] = None
    
    # Extended fields for new rules (optional, with defaults)
    emergency_fund_balance: Optional[float] = None
    rent_or_housing: Optional[float] = None
    weekly_expenses: Optional[List[float]] = None
    previous_month_income: Optional[float] = None
    previous_month_expense: Optional[float] = None
    large_transactions: Optional[List[float]] = None
    cash_withdrawals: Optional[float] = None
    loan_emi_total: Optional[float] = None
    zero_income_days: Optional[int] = None
    consecutive_deficit_count: Optional[int] = None
    previous_savings_balance: Optional[float] = None
    current_savings_balance: Optional[float] = None


class RuleTrigger(BaseModel):
    rule_id: str
    triggered: bool
    severity: Optional[Literal["low", "medium", "high"]] = None
    weight: float = 1.0  # Rule weight for risk scoring
    params: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
    data_refs: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    id: str
    dimension: Literal[
        "deficit", "overspend", "savings", "volatility", "stability", "discretionary", "category_outlier"
    ]
    score: float  # Weighted score (changed from int to float)
    severity: Literal["low", "medium", "high", "none"]
    summary: str
    reasons: List[str] = Field(default_factory=list)
    data_refs: List[str] = Field(default_factory=list)
    contributors: List[Dict[str, Any]] = Field(default_factory=list)
    weighted_score: Optional[float] = None  # Calculated weighted score
    max_possible_score: Optional[float] = None  # Maximum possible score for this dimension


class Recommendation(BaseModel):
    id: str
    title: str
    body: str
    actions: List[str]
    amounts: Dict[str, Any] = Field(default_factory=dict)
    linked_risks: List[str] = Field(default_factory=list)
    priority: int = 3
    valid_for_days: int = 30
    data_refs: List[str] = Field(default_factory=list)


class OutputModel(BaseModel):
    metadata: Dict[str, Any]
    risks: List[RiskItem]
    rule_triggers: List[RuleTrigger]
    recommendations: List[Recommendation]
    action_plan: Dict[str, Any]
    alerts: Optional[List[Dict[str, Any]]] = None
    audit: Optional[Dict[str, Any]] = None
