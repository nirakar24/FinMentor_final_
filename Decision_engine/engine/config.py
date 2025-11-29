from typing import Dict


DEFAULTS = {
    "currency": "₹",
    "persona_min_savings": {
        "gig_worker": 0.25,
        "salaried": 0.20,
        "default": 0.20,
    },
    "volatility_threshold": {
        "gig_worker": 0.30,
        "salaried": 0.20,
        "default": 0.25,
    },
    "stability_thresholds": {"low": 0.8, "high": 0.6},
    "overspend_bands": {"low": 0.10, "med": 0.20, "high": 0.35},
    "discretionary_ratio_bands": {"low": 0.25, "med": 0.35},
    "deficit_bands": {"low": 0.05, "med": 0.15},  # fraction of income
    "weights": {
        "deficit": 0.30,
        "overspend": 0.20,
        "volatility": 0.15,
        "stability": 0.15,
        "savings": 0.10,
        "discretionary": 0.05,
        "category_outlier": 0.05,
    },
    "discretionary_categories": {"Entertainment", "Leisure", "Eating Out", "Shopping"},
    "essential_min_caps": {"Utilities": 0.9, "Health": 0.9},  # won't cut below 90% baseline
    # Bucket 1: Budget Stability thresholds
    "emergency_fund_months": {"gig_worker": 6, "salaried": 3, "default": 3},
    "rent_income_ratio_max": 0.35,  # Housing should be ≤35% of income
    "weekly_spike_threshold": 1.5,  # 50% above average weekly spend
    "consecutive_deficit_months": 2,
    "savings_depletion_rate": 0.20,  # Alarm if savings dropping >20%/month
    # Bucket 2: Volatility & Risk thresholds
    "cashflow_variance_high": 0.30,  # CV of weekly cashflows
    "income_drop_threshold": 0.25,  # 25% drop month-over-month
    "large_transaction_ratio": 0.15,  # Single transaction >15% of monthly income
    "zero_income_days_max": 5,
    # Bucket 3: Category-Based thresholds
    "category_spike_threshold": 0.40,  # 40% increase in a category
    "food_income_ratio_max": 0.25,
    "transport_income_ratio_max": 0.15,
    "cash_withdrawal_spike": 0.50,  # 50% above average
    "loan_emi_income_ratio_max": 0.40,  # Total EMI should be ≤40%
    "category_thresholds": {
        "food": 0.30,  # Food should be <30% of total expenses
        "transport": 0.20,
        "entertainment": 0.15,
        "utilities": 0.12,
    },
    "rent_threshold": 0.35,  # Housing <35% of income
    "essential_threshold": 0.25,  # Utilities + Health <25%
    # Bucket 4: Forecast-Driven thresholds
    "forecast_deficit_threshold": 0.10,  # Predicted deficit >10% of income
    "forecast_surplus_threshold": 0.10,  # Predicted surplus >10% of income
    "buffer_months_warning": {"gig_worker": 4, "salaried": 2, "default": 2},
    "forecast_confidence_min": 0.70,
}


def persona_value(mapping: Dict[str, float], persona: str) -> float:
    return mapping.get(persona or "", mapping.get("default"))
