from __future__ import annotations
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class CategorySpend(BaseModel):
    # Accept arbitrary category keys dynamically via Dict
    __root__: Dict[str, float]

    def total(self) -> float:
        return float(sum(self.__root__.values()))

    def get(self, key: str, default: float = 0.0) -> float:
        return float(self.__root__.get(key, default))


class BehaviourMetrics(BaseModel):
    avg_daily_expense: Optional[float] = None
    high_spend_days: Optional[int] = None
    cashflow_stability: Optional[float] = None  # 0-1 (higher is better)
    discretionary_ratio: Optional[float] = None  # 0-1


class Forecast(BaseModel):
    predicted_income_next_month: Optional[float] = None
    predicted_expense_next_month: Optional[float] = None
    savings: Optional[float] = None
    confidence: Optional[float] = None


class InputPayload(BaseModel):
    user_id: str
    month: str

    avg_monthly_income: Optional[float] = None
    avg_monthly_expense: Optional[float] = None

    current_month_income: Optional[float] = None
    current_month_expense: Optional[float] = None

    savings_rate: Optional[float] = None  # 0-1
    income_volatility: Optional[float] = None  # 0-1
    risk_level: Optional[Literal["low", "moderate", "high"]] = None

    Category_spend: Optional[Dict[str, float]] = Field(default=None)
    Behaviour_metrics: Optional[BehaviourMetrics] = Field(default=None)
    Forecast: Optional[Forecast] = Field(default=None)

    persona_type: Optional[str] = None
    confidence_score: Optional[float] = None
    last_updated: Optional[str] = None

    insights: Optional[Dict[str, str]] = None

    @field_validator("savings_rate", "income_volatility", mode="before")
    @classmethod
    def clamp_rate(cls, v):
        if v is None:
            return v
        try:
            v = float(v)
        except Exception:
            return None
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v


class RuleTrigger(BaseModel):
    rule_id: str
    triggered: bool
    severity: Optional[Literal["low", "medium", "high"]] = None
    params: Dict[str, float] = Field(default_factory=dict)
    reason: Optional[str] = None
    data_refs: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    id: str
    dimension: Literal[
        "deficit",
        "overspend",
        "savings",
        "volatility",
        "stability",
        "discretionary",
        "category_outlier",
    ]
    score: int
    severity: Literal["low", "medium", "high"]
    summary: str
    reasons: List[str] = Field(default_factory=list)
    data_refs: List[str] = Field(default_factory=list)
    contributors: List[Dict[str, str]] = Field(default_factory=list)
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


class Recommendation(BaseModel):
    id: str
    title: str
    body: str
    actions: List[str] = Field(default_factory=list)
    amounts: Dict[str, float] = Field(default_factory=dict)
    linked_risks: List[str] = Field(default_factory=list)
    priority: int = 3
    valid_for_days: int = 30
    data_refs: List[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    action_id: str
    title: str
    kpi: Optional[str] = None
    target: Optional[str] = None
    due_by: Optional[str] = None
    owner: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)


class ActionPlan(BaseModel):
    next_30_days: List[ActionItem] = Field(default_factory=list)
    next_90_days: List[ActionItem] = Field(default_factory=list)
    kpis: List[Dict[str, str]] = Field(default_factory=list)


class OutputPayload(BaseModel):
    metadata: Dict[str, str]
    risks: List[RiskItem]
    rule_triggers: List[RuleTrigger]
    recommendations: List[Recommendation]
    action_plan: ActionPlan
    alerts: Optional[List[Dict[str, str]]] = None
    audit: Optional[Dict[str, object]] = None
