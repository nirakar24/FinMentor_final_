from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .models import NormalizedInput, RuleTrigger
from .config import DEFAULTS, persona_value


def _severity_from_fraction(frac: float, low: float, med: float) -> str:
    if frac < low:
        return "low"
    if frac < med:
        return "medium"
    return "high"


def eval_rules(data: NormalizedInput) -> List[RuleTrigger]:
    rules: List[RuleTrigger] = []
    persona = data.persona_type or "default"
    
    # Extract commonly used nested objects
    behavior = data.behavior_metrics
    forecast = data.forecast
    insights = data.insights

    # ========================================
    # BUCKET 1: BUDGET STABILITY RULES (10)
    # ========================================

    # R-DEFICIT-01 (existing)
    gap = data.current_month_expense - data.current_month_income
    deficit_triggered = gap > 0
    if deficit_triggered:
        income = max(data.current_month_income, 1e-6)
        gap_pct = gap / income
        sev = _severity_from_fraction(gap_pct, DEFAULTS["deficit_bands"]["low"], DEFAULTS["deficit_bands"]["med"])
        rules.append(
            RuleTrigger(
                rule_id="R-DEFICIT-01",
                triggered=True,
                severity=sev,
                params={"gap_amt": gap, "gap_pct_income": gap_pct},
                reason="Current expenses exceed current income",
                data_refs=["/current_month_expense", "/current_month_income"],
            )
        )
    else:
        rules.append(RuleTrigger(rule_id="R-DEFICIT-01", triggered=False))

    # R-OVRSPEND-01
    if data.expense_delta_pct is not None and data.expense_delta_pct > DEFAULTS["overspend_bands"]["low"]:
        delta = data.expense_delta_pct
        sev = "low"
        if delta > DEFAULTS["overspend_bands"]["high"]:
            sev = "high"
        elif delta > DEFAULTS["overspend_bands"]["med"]:
            sev = "medium"
        rules.append(
            RuleTrigger(
                rule_id="R-OVRSPEND-01",
                triggered=True,
                severity=sev,
                params={"delta_pct": delta},
                reason="Current expenses above average",
                data_refs=["/current_month_expense", "/avg_monthly_expense"],
            )
        )
    else:
        rules.append(RuleTrigger(rule_id="R-OVRSPEND-01", triggered=False))

    # R-EMERG-FUND-01: No or insufficient emergency fund
    if data.emergency_fund_balance is not None and data.avg_monthly_expense:
        required_months = persona_value(DEFAULTS["emergency_fund_months"], persona)
        required_fund = required_months * data.avg_monthly_expense
        if data.emergency_fund_balance < required_fund:
            shortfall = required_fund - data.emergency_fund_balance
            gap_ratio = shortfall / required_fund
            sev = "high" if gap_ratio > 0.7 else "medium" if gap_ratio > 0.4 else "low"
            rules.append(
                RuleTrigger(
                    rule_id="R-EMERG-FUND-01",
                    triggered=True,
                    severity=sev,
                    params={"current_fund": data.emergency_fund_balance, "required_fund": required_fund, "shortfall": shortfall},
                    reason=f"Emergency fund is {shortfall:.0f} short of {required_months}-month target",
                    data_refs=["/emergency_fund_balance", "/avg_monthly_expense"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-EMERG-FUND-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-EMERG-FUND-01", triggered=False))

    # R-RENT-HIGH-01: Rent/housing exceeds 35% of income
    if data.rent_or_housing is not None and data.current_month_income:
        rent_ratio = data.rent_or_housing / max(data.current_month_income, 1e-6)
        if rent_ratio > DEFAULTS["rent_income_ratio_max"]:
            excess = rent_ratio - DEFAULTS["rent_income_ratio_max"]
            sev = "high" if rent_ratio > 0.50 else "medium" if rent_ratio > 0.40 else "low"
            rules.append(
                RuleTrigger(
                    rule_id="R-RENT-HIGH-01",
                    triggered=True,
                    severity=sev,
                    params={"rent_ratio": rent_ratio, "rent_amount": data.rent_or_housing},
                    reason=f"Housing cost is {rent_ratio*100:.1f}% of income (max recommended: 35%)",
                    data_refs=["/rent_or_housing", "/current_month_income"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-RENT-HIGH-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-RENT-HIGH-01", triggered=False))

    # R-WEEKLY-SPIKE-01: Weekly spend spike detected
    if data.weekly_expenses and len(data.weekly_expenses) >= 2:
        avg_weekly = sum(data.weekly_expenses) / len(data.weekly_expenses)
        max_weekly = max(data.weekly_expenses)
        if avg_weekly > 0 and max_weekly > avg_weekly * DEFAULTS["weekly_spike_threshold"]:
            spike_ratio = max_weekly / avg_weekly
            sev = "high" if spike_ratio > 2.0 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-WEEKLY-SPIKE-01",
                    triggered=True,
                    severity=sev,
                    params={"max_weekly": max_weekly, "avg_weekly": avg_weekly, "spike_ratio": spike_ratio},
                    reason=f"One week's spending was {spike_ratio:.1f}x the average",
                    data_refs=["/weekly_expenses"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-WEEKLY-SPIKE-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-WEEKLY-SPIKE-01", triggered=False))

    # R-CONSEC-DEF-01: Consecutive deficit months
    if data.consecutive_deficit_count is not None:
        if data.consecutive_deficit_count >= DEFAULTS["consecutive_deficit_months"]:
            sev = "high" if data.consecutive_deficit_count >= 3 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-CONSEC-DEF-01",
                    triggered=True,
                    severity=sev,
                    params={"consecutive_months": data.consecutive_deficit_count},
                    reason=f"Deficit for {data.consecutive_deficit_count} consecutive months",
                    data_refs=["/consecutive_deficit_count"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-CONSEC-DEF-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-CONSEC-DEF-01", triggered=False))

    # R-SAVE-DEPLETE-01: Savings depleting rapidly
    if data.previous_savings_balance is not None and data.current_savings_balance is not None and data.previous_savings_balance > 0:
        depletion = (data.previous_savings_balance - data.current_savings_balance) / data.previous_savings_balance
        if depletion > DEFAULTS["savings_depletion_rate"]:
            sev = "high" if depletion > 0.40 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-SAVE-DEPLETE-01",
                    triggered=True,
                    severity=sev,
                    params={"depletion_rate": depletion, "prev_balance": data.previous_savings_balance, "current_balance": data.current_savings_balance},
                    reason=f"Savings dropped by {depletion*100:.1f}% this month",
                    data_refs=["/previous_savings_balance", "/current_savings_balance"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-SAVE-DEPLETE-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-SAVE-DEPLETE-01", triggered=False))

    # R-FCAST-DEF-01 (existing, moved here for organization)
    if data.forecast and data.forecast.predicted_expense_next_month is not None and data.forecast.predicted_income_next_month is not None:
        if data.forecast.predicted_expense_next_month > data.forecast.predicted_income_next_month and (data.forecast.confidence or 0) >= 0.7:
            gap_f = data.forecast.predicted_expense_next_month - data.forecast.predicted_income_next_month
            income_f = max(data.forecast.predicted_income_next_month, 1e-6)
            gap_f_pct = gap_f / income_f
            sev = _severity_from_fraction(gap_f_pct, DEFAULTS["deficit_bands"]["low"], DEFAULTS["deficit_bands"]["med"])
            rules.append(
                RuleTrigger(
                    rule_id="R-FCAST-DEF-01",
                    triggered=True,
                    severity=sev,
                    params={"gap_amt": gap_f, "gap_pct_income": gap_f_pct},
                    reason="Forecasted expenses exceed forecasted income",
                    data_refs=[
                        "/Forecast/predicted_expense_next_month",
                        "/Forecast/predicted_income_next_month",
                        "/Forecast/confidence",
                    ],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-FCAST-DEF-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-FCAST-DEF-01", triggered=False))

    # R-SAVE-LOW-01 (existing)
    if data.savings_rate is not None:
        min_save = persona_value(DEFAULTS["persona_min_savings"], persona)
        if data.savings_rate < min_save:
            sev = "high" if data.savings_rate < min_save * 0.5 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-SAVE-LOW-01",
                    triggered=True,
                    severity=sev,
                    params={"current_rate": data.savings_rate, "target_rate": min_save},
                    reason="Savings rate below persona target",
                    data_refs=["/savings_rate"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-SAVE-LOW-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-SAVE-LOW-01", triggered=False))

    # ========================================
    # BUCKET 2: VOLATILITY & RISK RULES (8)
    # ========================================

    # R-VOL-INC-01 (existing)
    if data.income_volatility is not None:
        thr = persona_value(DEFAULTS["volatility_threshold"], persona)
        if data.income_volatility > thr:
            sev = "high" if data.income_volatility > thr * 1.5 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-VOL-INC-01",
                    triggered=True,
                    severity=sev,
                    params={"income_volatility": data.income_volatility, "threshold": thr},
                    reason="Income volatility above threshold",
                    data_refs=["/income_volatility"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-VOL-INC-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-VOL-INC-01", triggered=False))

    # R-STAB-LOW-01
    stab = behavior.cashflow_stability if behavior else None
    if stab is not None:
        sev = None
        if stab < DEFAULTS["stability_thresholds"]["high"]:
            sev = "high"
        elif stab < DEFAULTS["stability_thresholds"]["low"]:
            sev = "medium"
        if sev:
            rules.append(
                RuleTrigger(
                    rule_id="R-STAB-LOW-01",
                    triggered=True,
                    severity=sev,
                    params={"cashflow_stability": stab},
                    reason="Cashflow stability is low",
                    data_refs=["/Behaviour_metrics/cashflow_stability", "/behavior_metrics/cashflow_stability"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-STAB-LOW-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-STAB-LOW-01", triggered=False))

    # R-DISC-HIGH-01
    disc = behavior.discretionary_ratio if behavior else None
    if disc is not None and disc > DEFAULTS["discretionary_ratio_bands"]["low"]:
        sev = "medium" if disc <= DEFAULTS["discretionary_ratio_bands"]["med"] else "high"
        rules.append(
            RuleTrigger(
                rule_id="R-DISC-HIGH-01",
                triggered=True,
                severity=sev,
                params={"discretionary_ratio": disc},
                reason="High discretionary spending ratio",
                data_refs=["/Behaviour_metrics/discretionary_ratio", "/behavior_metrics/discretionary_ratio"],
            )
        )
    else:
        rules.append(RuleTrigger(rule_id="R-DISC-HIGH-01", triggered=False))

    # R-HSD-01
    hsd = behavior.high_spend_days if behavior else None
    if hsd is not None and hsd > 6:
        sev = "high" if hsd > 10 else "medium"
        rules.append(
            RuleTrigger(
                rule_id="R-HSD-01",
                triggered=True,
                severity=sev,
                params={"high_spend_days": hsd},
                reason="High number of high-spend days",
                data_refs=["/Behaviour_metrics/high_spend_days", "/behavior_metrics/high_spend_days"],
            )
        )
    else:
        rules.append(RuleTrigger(rule_id="R-HSD-01", triggered=False))

    # R-INCOME-DROP-01: Significant income drop month-over-month
    if data.previous_month_income is not None and data.current_month_income and data.previous_month_income > 0:
        income_drop = (data.previous_month_income - data.current_month_income) / data.previous_month_income
        if income_drop > DEFAULTS["income_drop_threshold"]:
            sev = "high" if income_drop > 0.40 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-INCOME-DROP-01",
                    triggered=True,
                    severity=sev,
                    params={"drop_pct": income_drop, "prev_income": data.previous_month_income, "current_income": data.current_month_income},
                    reason=f"Income dropped by {income_drop*100:.1f}% from last month",
                    data_refs=["/previous_month_income", "/current_month_income"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-INCOME-DROP-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-INCOME-DROP-01", triggered=False))

    # R-LARGE-TXN-01: Large transaction detected
    if data.large_transactions and data.current_month_income:
        max_txn = max(data.large_transactions) if data.large_transactions else 0
        txn_ratio = max_txn / max(data.current_month_income, 1e-6)
        if txn_ratio > DEFAULTS["large_transaction_ratio"]:
            sev = "medium" if txn_ratio <= 0.30 else "high"
            rules.append(
                RuleTrigger(
                    rule_id="R-LARGE-TXN-01",
                    triggered=True,
                    severity=sev,
                    params={"transaction_amount": max_txn, "income_ratio": txn_ratio},
                    reason=f"Single transaction of {max_txn:.0f} is {txn_ratio*100:.1f}% of monthly income",
                    data_refs=["/large_transactions", "/current_month_income"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-LARGE-TXN-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-LARGE-TXN-01", triggered=False))

    # R-ZERO-INC-DAYS-01: Too many zero-income days
    if data.zero_income_days is not None:
        if data.zero_income_days > DEFAULTS["zero_income_days_max"]:
            sev = "high" if data.zero_income_days > 10 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-ZERO-INC-DAYS-01",
                    triggered=True,
                    severity=sev,
                    params={"zero_income_days": data.zero_income_days},
                    reason=f"{data.zero_income_days} days with zero income detected",
                    data_refs=["/zero_income_days"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-ZERO-INC-DAYS-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-ZERO-INC-DAYS-01", triggered=False))

    # R-CASHFLOW-VAR-01: High cashflow variance
    if data.weekly_expenses and len(data.weekly_expenses) >= 3:
        import statistics
        mean_weekly = statistics.mean(data.weekly_expenses)
        if mean_weekly > 0:
            stdev_weekly = statistics.stdev(data.weekly_expenses)
            cv = stdev_weekly / mean_weekly
            if cv > DEFAULTS["cashflow_variance_high"]:
                sev = "high" if cv > 0.50 else "medium"
                rules.append(
                    RuleTrigger(
                        rule_id="R-CASHFLOW-VAR-01",
                        triggered=True,
                        severity=sev,
                        params={"coefficient_of_variation": cv},
                        reason=f"Cashflow variance is high (CV={cv:.2f})",
                        data_refs=["/weekly_expenses"],
                    )
                )
            else:
                rules.append(RuleTrigger(rule_id="R-CASHFLOW-VAR-01", triggered=False))
        else:
            rules.append(RuleTrigger(rule_id="R-CASHFLOW-VAR-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-CASHFLOW-VAR-01", triggered=False))

    # ========================================
    # BUCKET 3: CATEGORY-BASED RULES (7)
    # ========================================

    # R-CAT-DRIFT-01 (existing, parse string like "Entertainment up by 40%")
    drift = insights.category_drift if insights else None
    if drift:
        m = re.search(r"(\w[\w\s&-]*)\s+up\s+by\s+(\d+)%", drift, re.IGNORECASE)
        if m:
            cat = m.group(1).strip()
            pct = float(m.group(2)) / 100.0
            if pct >= 0.3:
                sev = "high" if pct >= 0.5 else "medium"
                rules.append(
                    RuleTrigger(
                        rule_id="R-CAT-DRIFT-01",
                        triggered=True,
                        severity=sev,
                        params={"category": cat, "delta_pct": pct},
                        reason=f"Category {cat} increased by {int(pct*100)}%",
                        data_refs=["/insights/category_drift"],
                    )
                )
            else:
                rules.append(RuleTrigger(rule_id="R-CAT-DRIFT-01", triggered=False))
        else:
            rules.append(RuleTrigger(rule_id="R-CAT-DRIFT-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-CAT-DRIFT-01", triggered=False))

    # R-TOP-CAT-HEAVY-01
    if insights and insights.top_spend_category:
        total_exp = data.current_month_expense or sum(data.category_spend.values())
        if total_exp:
            cat = insights.top_spend_category
            share = (data.category_spend.get(cat, 0.0)) / total_exp
            if share > 0.25:
                sev = "high" if share > 0.4 else "medium"
                rules.append(
                    RuleTrigger(
                        rule_id="R-TOP-CAT-HEAVY-01",
                        triggered=True,
                        severity=sev,
                        params={"category": cat, "share": share},
                        reason=f"Top category {cat} is {int(share*100)}% of spend",
                        data_refs=["/insights/top_spend_category", "/Category_spend"],
                    )
                )
            else:
                rules.append(RuleTrigger(rule_id="R-TOP-CAT-HEAVY-01", triggered=False))
        else:
            rules.append(RuleTrigger(rule_id="R-TOP-CAT-HEAVY-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-TOP-CAT-HEAVY-01", triggered=False))

    # R-FOOD-HIGH-01: Food expenses exceed threshold
    if data.category_spend.get("Food", 0) and data.current_month_income:
        food_ratio = data.category_spend["Food"] / max(data.current_month_income, 1e-6)
        if food_ratio > DEFAULTS["food_income_ratio_max"]:
            sev = "high" if food_ratio > 0.35 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-FOOD-HIGH-01",
                    triggered=True,
                    severity=sev,
                    params={"food_amount": data.category_spend["Food"], "income_ratio": food_ratio},
                    reason=f"Food spending is {food_ratio*100:.1f}% of income (recommended: ≤25%)",
                    data_refs=["/Category_spend/Food", "/current_month_income"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-FOOD-HIGH-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-FOOD-HIGH-01", triggered=False))

    # R-TRANSPORT-HIGH-01: Transport expenses exceed threshold
    if data.category_spend.get("Transport", 0) and data.current_month_income:
        transport_ratio = data.category_spend["Transport"] / max(data.current_month_income, 1e-6)
        if transport_ratio > DEFAULTS["transport_income_ratio_max"]:
            sev = "high" if transport_ratio > 0.25 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-TRANSPORT-HIGH-01",
                    triggered=True,
                    severity=sev,
                    params={"transport_amount": data.category_spend["Transport"], "income_ratio": transport_ratio},
                    reason=f"Transport spending is {transport_ratio*100:.1f}% of income (recommended: ≤15%)",
                    data_refs=["/Category_spend/Transport", "/current_month_income"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-TRANSPORT-HIGH-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-TRANSPORT-HIGH-01", triggered=False))

    # R-CASH-SPIKE-01: Cash withdrawal spike
    if data.cash_withdrawals is not None and data.current_month_expense:
        # Assume avg cash is 10% of expense baseline
        avg_cash = data.avg_monthly_expense * 0.10 if data.avg_monthly_expense else 0
        if avg_cash > 0 and data.cash_withdrawals > avg_cash * (1 + DEFAULTS["cash_withdrawal_spike"]):
            spike_ratio = data.cash_withdrawals / avg_cash
            sev = "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-CASH-SPIKE-01",
                    triggered=True,
                    severity=sev,
                    params={"cash_amount": data.cash_withdrawals, "spike_ratio": spike_ratio},
                    reason=f"Cash withdrawals are {spike_ratio:.1f}x the average",
                    data_refs=["/cash_withdrawals"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-CASH-SPIKE-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-CASH-SPIKE-01", triggered=False))

    # R-LOAN-EMI-HIGH-01: Loan/EMI burden too high
    if data.loan_emi_total is not None and data.current_month_income:
        emi_ratio = data.loan_emi_total / max(data.current_month_income, 1e-6)
        if emi_ratio > DEFAULTS["loan_emi_income_ratio_max"]:
            sev = "high" if emi_ratio > 0.50 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-LOAN-EMI-HIGH-01",
                    triggered=True,
                    severity=sev,
                    params={"emi_total": data.loan_emi_total, "income_ratio": emi_ratio},
                    reason=f"Loan EMI is {emi_ratio*100:.1f}% of income (recommended: ≤40%)",
                    data_refs=["/loan_emi_total", "/current_month_income"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-LOAN-EMI-HIGH-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-LOAN-EMI-HIGH-01", triggered=False))

    # R-UTILITIES-SPIKE-01: Utilities category spike
    utilities_current = data.category_spend.get("Utilities", 0)
    # Assume avg utilities baseline from avg_monthly_expense proportionally
    if utilities_current > 0 and data.avg_monthly_expense:
        # Estimate baseline: utilities should be ~10-12% of expense
        utilities_baseline = data.avg_monthly_expense * 0.11
        if utilities_current > utilities_baseline * (1 + DEFAULTS["category_spike_threshold"]):
            spike_ratio = utilities_current / utilities_baseline
            sev = "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-UTILITIES-SPIKE-01",
                    triggered=True,
                    severity=sev,
                    params={"utilities_amount": utilities_current, "spike_ratio": spike_ratio},
                    reason=f"Utilities spending is {spike_ratio:.1f}x the expected baseline",
                    data_refs=["/Category_spend/Utilities"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-UTILITIES-SPIKE-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-UTILITIES-SPIKE-01", triggered=False))

    # ========================================
    # BUCKET 4: FORECAST-DRIVEN RULES (5)
    # ========================================

    # R-FCAST-SURPLUS-01: Predicted surplus
    if forecast and forecast.predicted_income_next_month is not None and forecast.predicted_expense_next_month is not None:
        surplus = forecast.predicted_income_next_month - forecast.predicted_expense_next_month
        if surplus > 0 and forecast.predicted_income_next_month > 0:
            surplus_ratio = surplus / forecast.predicted_income_next_month
            if surplus_ratio > DEFAULTS["forecast_surplus_threshold"] and (forecast.confidence or 0) >= DEFAULTS["forecast_confidence_min"]:
                sev = "low"  # Positive signal, low severity
                rules.append(
                    RuleTrigger(
                        rule_id="R-FCAST-SURPLUS-01",
                        triggered=True,
                        severity=sev,
                        params={"surplus_amount": surplus, "surplus_ratio": surplus_ratio},
                        reason=f"Forecasted surplus of {surplus:.0f} ({surplus_ratio*100:.1f}% of income) next month",
                        data_refs=["/Forecast/predicted_income_next_month", "/Forecast/predicted_expense_next_month"],
                    )
                )
            else:
                rules.append(RuleTrigger(rule_id="R-FCAST-SURPLUS-01", triggered=False))
        else:
            rules.append(RuleTrigger(rule_id="R-FCAST-SURPLUS-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-FCAST-SURPLUS-01", triggered=False))

    # R-BUFFER-WARN-01: Buffer dropping below warning threshold
    if data.emergency_fund_balance is not None and data.avg_monthly_expense:
        buffer_months = data.emergency_fund_balance / max(data.avg_monthly_expense, 1e-6)
        warn_months = persona_value(DEFAULTS["buffer_months_warning"], persona)
        if buffer_months < warn_months:
            sev = "high" if buffer_months < warn_months * 0.5 else "medium"
            rules.append(
                RuleTrigger(
                    rule_id="R-BUFFER-WARN-01",
                    triggered=True,
                    severity=sev,
                    params={"buffer_months": buffer_months, "warning_threshold": warn_months},
                    reason=f"Buffer covers only {buffer_months:.1f} months (recommended: ≥{warn_months})",
                    data_refs=["/emergency_fund_balance", "/avg_monthly_expense"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-BUFFER-WARN-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-BUFFER-WARN-01", triggered=False))

    # R-FCAST-CONF-LOW-01: Forecast confidence too low
    if forecast and forecast.confidence is not None:
        if forecast.confidence < DEFAULTS["forecast_confidence_min"]:
            sev = "low"
            rules.append(
                RuleTrigger(
                    rule_id="R-FCAST-CONF-LOW-01",
                    triggered=True,
                    severity=sev,
                    params={"confidence": forecast.confidence},
                    reason=f"Forecast confidence is {forecast.confidence:.2f} (below threshold {DEFAULTS['forecast_confidence_min']:.2f})",
                    data_refs=["/Forecast/confidence"],
                )
            )
        else:
            rules.append(RuleTrigger(rule_id="R-FCAST-CONF-LOW-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-FCAST-CONF-LOW-01", triggered=False))

    # R-FCAST-DEF-LARGE-01: Forecasted deficit is large (>10% of income)
    if forecast and forecast.predicted_expense_next_month is not None and forecast.predicted_income_next_month is not None:
        deficit_f = forecast.predicted_expense_next_month - forecast.predicted_income_next_month
        if deficit_f > 0 and forecast.predicted_income_next_month > 0:
            deficit_ratio = deficit_f / forecast.predicted_income_next_month
            if deficit_ratio > DEFAULTS["forecast_deficit_threshold"] and (forecast.confidence or 0) >= DEFAULTS["forecast_confidence_min"]:
                sev = "high" if deficit_ratio > 0.20 else "medium"
                rules.append(
                    RuleTrigger(
                        rule_id="R-FCAST-DEF-LARGE-01",
                        triggered=True,
                        severity=sev,
                        params={"deficit_amount": deficit_f, "deficit_ratio": deficit_ratio},
                        reason=f"Forecasted deficit is {deficit_ratio*100:.1f}% of next month's income",
                        data_refs=["/Forecast/predicted_expense_next_month", "/Forecast/predicted_income_next_month"],
                    )
                )
            else:
                rules.append(RuleTrigger(rule_id="R-FCAST-DEF-LARGE-01", triggered=False))
        else:
            rules.append(RuleTrigger(rule_id="R-FCAST-DEF-LARGE-01", triggered=False))
    else:
        rules.append(RuleTrigger(rule_id="R-FCAST-DEF-LARGE-01", triggered=False))

    return rules
