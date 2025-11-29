from __future__ import annotations

from typing import Any, Dict

from .models import NormalizedInput, BehaviorMetrics, Forecast, Insights


def _get(d: Dict[str, Any], *keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def normalize_input(raw: Dict[str, Any]) -> NormalizedInput:
    if not isinstance(raw, dict):
        raise ValueError("Input must be a JSON object")

    # Standardize to snake_case (SCHEMA-01)
    category_spend = _get(raw, "category_spend", "Category_spend", default={}) or {}
    behavior = _get(raw, "behavior_metrics", "Behaviour_metrics", default={}) or {}
    forecast = _get(raw, "forecast", "Forecast", default=None) or None
    insights = raw.get("insights") or None

    bmi = BehaviorMetrics(**behavior) if behavior else None
    fct = Forecast(**forecast) if forecast else None
    ins = Insights(**insights) if insights else None

    # Safe numeric extraction with defaults (handles None values)
    # Use 'or 0' to convert None to 0 before float() conversion
    try:
        avg_income = float(raw.get("avg_monthly_income") or 0)
        avg_expense = float(raw.get("avg_monthly_expense") or 0)
        cur_income = float(raw.get("current_month_income") or 0)
        cur_expense = float(raw.get("current_month_expense") or 0)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Numeric field conversion error: {e}. Ensure all numeric fields are valid numbers.")
    
    # Critical validation: Reject zero or negative income (VALID-01, INC-01)
    if cur_income <= 0:
        raise ValueError(f"current_month_income must be positive, got {cur_income}")
    if avg_income <= 0:
        raise ValueError(f"avg_monthly_income must be positive, got {avg_income}")
    
    net_cashflow = cur_income - cur_expense
    expense_delta_pct = None
    if avg_expense:
        expense_delta_pct = (cur_expense - avg_expense) / avg_expense

    model = NormalizedInput(
        user_id=str(raw.get("user_id")),
        month=str(raw.get("month")),
        avg_monthly_income=avg_income,
        avg_monthly_expense=avg_expense,
        current_month_income=cur_income,
        current_month_expense=cur_expense,
        savings_rate=raw.get("savings_rate"),
        income_volatility=raw.get("income_volatility"),
        risk_level=raw.get("risk_level"),
        category_spend={str(k): float(v) for k, v in (category_spend or {}).items()},
        behavior_metrics=bmi,
        forecast=fct,
        persona_type=raw.get("persona_type"),
        confidence_score=raw.get("confidence_score"),
        last_updated=raw.get("last_updated"),
        insights=ins,
        net_cashflow=net_cashflow,
        expense_delta_pct=expense_delta_pct,
    )
    return model
