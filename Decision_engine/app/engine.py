from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime

from .schemas import (
    InputPayload,
    OutputPayload,
    ActionPlan,
    RiskItem,
    RuleTrigger,
    Recommendation,
)

ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "2025-11-16"


def _severity_from_ratio(r: float) -> str:
    if r >= 0.35:
        return "high"
    if r >= 0.2:
        return "medium"
    if r > 0:
        return "low"
    return "low"


def _band_to_score(band: str) -> int:
    return {"low": 33, "medium": 66, "high": 100}.get(band, 0)


def _aggregate_severity(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _persona_settings(persona: str) -> Dict:
    persona = (persona or "").lower()
    if persona == "gig_worker":
        return {
            "weights": {
                "deficit": 0.30,
                "overspend": 0.20,
                "volatility": 0.20,
                "stability": 0.15,
                "savings": 0.10,
                "discretionary": 0.03,
                "category_outlier": 0.02,
            },
            "savings_min": 0.25,
            "volatility_high": 0.30,
        }
    if persona == "salaried":
        return {
            "weights": {
                "deficit": 0.35,
                "overspend": 0.25,
                "volatility": 0.10,
                "stability": 0.15,
                "savings": 0.10,
                "discretionary": 0.03,
                "category_outlier": 0.02,
            },
            "savings_min": 0.20,
            "volatility_high": 0.20,
        }
    # default
    return {
        "weights": {
            "deficit": 0.30,
            "overspend": 0.20,
            "volatility": 0.15,
            "stability": 0.15,
            "savings": 0.10,
            "discretionary": 0.05,
            "category_outlier": 0.05,
        },  
        "savings_min": 0.20,
        "volatility_high": 0.25,
    }


def evaluate(input_data: InputPayload, currency: str = "₹") -> OutputPayload:
    now_iso = datetime.utcnow().isoformat() + "Z"

    # Convenience variables
    avg_inc = float(input_data.avg_monthly_income or 0.0)
    avg_exp = float(input_data.avg_monthly_expense or 0.0)
    cur_inc = float(input_data.current_month_income or 0.0)
    cur_exp = float(input_data.current_month_expense or 0.0)
    savings_rate = float(input_data.savings_rate or 0.0)
    income_vol = float(input_data.income_volatility or 0.0)

    category_map = input_data.Category_spend or {}
    beh = input_data.Behaviour_metrics
    forecast = input_data.Forecast

    # Derived
    net = cur_inc - cur_exp
    expense_delta_pct = (cur_exp - avg_exp) / avg_exp if avg_exp > 0 else 0.0

    cashflow_stability = float(getattr(beh, "cashflow_stability", 0.0) or 0.0)
    discretionary_ratio = float(getattr(beh, "discretionary_ratio", 0.0) or 0.0)
    high_spend_days = int(getattr(beh, "high_spend_days", 0) or 0)

    f_conf = float(getattr(forecast, "confidence", 1.0) or 1.0)
    conf = float(input_data.confidence_score or 1.0)

    persona = (input_data.persona_type or "").lower()
    settings = _persona_settings(persona)
    weights = settings["weights"]

    rule_triggers: List[RuleTrigger] = []
    risks: List[RiskItem] = []
    recs: List[Recommendation] = []

    # Rules
    # R-DEFICIT-01
    r_deficit = cur_exp > cur_inc
    gap_amt = max(0.0, cur_exp - cur_inc)
    gap_pct_income = (gap_amt / cur_inc) if cur_inc > 0 else 0.0
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-DEFICIT-01",
            triggered=r_deficit,
            severity=("high" if gap_pct_income > 0.15 else "medium" if gap_pct_income > 0.05 else "low") if r_deficit else None,
            params={"gap_amt": round(gap_amt, 2), "gap_pct_income": round(gap_pct_income, 4)},
            reason="current_month_expense exceeds current_month_income" if r_deficit else None,
            data_refs=["/current_month_expense", "/current_month_income"],
        )
    )

    # R-OVRSPEND-01
    r_overspend = expense_delta_pct > 0.1
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-OVRSPEND-01",
            triggered=r_overspend,
            severity=("high" if expense_delta_pct > 0.35 else "medium" if expense_delta_pct > 0.2 else "low") if r_overspend else None,
            params={"expense_delta_pct": round(expense_delta_pct, 4)},
            reason="current_month_expense exceeds average monthly expense by >10%" if r_overspend else None,
            data_refs=["/current_month_expense", "/avg_monthly_expense"],
        )
    )

    # R-FCAST-DEF-01
    f_deficit = False
    if forecast and forecast.predicted_income_next_month is not None and forecast.predicted_expense_next_month is not None:
        f_deficit = forecast.predicted_expense_next_month > forecast.predicted_income_next_month and f_conf >= 0.7
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-FCAST-DEF-01",
            triggered=bool(f_deficit),
            severity="medium" if f_deficit else None,
            params={},
            reason="Forecast predicts expenses exceeding income with adequate confidence" if f_deficit else None,
            data_refs=["/Forecast/predicted_expense_next_month", "/Forecast/predicted_income_next_month", "/Forecast/confidence"],
        )
    )

    # R-SAVE-LOW-01
    persona_min = settings["savings_min"]
    r_save_low = savings_rate < persona_min
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-SAVE-LOW-01",
            triggered=r_save_low,
            severity=("high" if savings_rate < 0.1 else "medium") if r_save_low else None,
            params={"savings_rate": round(savings_rate, 4), "persona_min": persona_min},
            reason="savings_rate below persona minimum",
            data_refs=["/savings_rate"],
        )
    )

    # R-VOL-INC-01
    vol_high_thr = settings["volatility_high"]
    r_vol_high = income_vol > vol_high_thr
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-VOL-INC-01",
            triggered=r_vol_high,
            severity=("high" if income_vol > max(vol_high_thr + 0.1, 0.35) else "medium") if r_vol_high else None,
            params={"income_volatility": round(income_vol, 4), "threshold": vol_high_thr},
            reason="income_volatility exceeds persona threshold" if r_vol_high else None,
            data_refs=["/income_volatility"],
        )
    )

    # R-STAB-LOW-01
    r_stab_low = cashflow_stability < 0.8 if beh and beh.cashflow_stability is not None else False
    stab_sev = "high" if cashflow_stability < 0.6 else "medium"
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-STAB-LOW-01",
            triggered=r_stab_low,
            severity=stab_sev if r_stab_low else None,
            params={"cashflow_stability": round(cashflow_stability, 4)},
            reason="cashflow_stability below target band" if r_stab_low else None,
            data_refs=["/Behaviour_metrics/cashflow_stability"],
        )
    )

    # R-DISC-HIGH-01
    r_disc_high = discretionary_ratio > 0.35 if beh and beh.discretionary_ratio is not None else False
    disc_sev = "high" if discretionary_ratio > 0.35 else "medium"
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-DISC-HIGH-01",
            triggered=r_disc_high,
            severity=disc_sev if r_disc_high else None,
            params={"discretionary_ratio": round(discretionary_ratio, 4)},
            reason="discretionary ratio above recommended bound" if r_disc_high else None,
            data_refs=["/Behaviour_metrics/discretionary_ratio"],
        )
    )

    # R-HSD-01
    r_hsd = high_spend_days > 6 if beh and beh.high_spend_days is not None else False
    hsd_sev = "high" if high_spend_days > 10 else "medium"
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-HSD-01",
            triggered=r_hsd,
            severity=hsd_sev if r_hsd else None,
            params={"high_spend_days": high_spend_days},
            reason="high number of high-spend days" if r_hsd else None,
            data_refs=["/Behaviour_metrics/high_spend_days"],
        )
    )

    # R-TOP-CAT-HEAVY-01 and R-CAT-DRIFT-01 (simplified):
    top_cat = None
    top_share = 0.0
    total_exp = cur_exp if cur_exp > 0 else sum(category_map.values()) if category_map else 0.0
    if category_map and total_exp > 0:
        for k, v in category_map.items():
            share = (v or 0.0) / total_exp
            if share > top_share:
                top_share = share
                top_cat = k
    r_top_heavy = top_share > 0.25 if total_exp > 0 else False
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-TOP-CAT-HEAVY-01",
            triggered=bool(r_top_heavy),
            severity="medium" if r_top_heavy else None,
            params={"category": top_cat or "", "share": round(top_share, 4)},
            reason="Top category exceeds 25% of spend" if r_top_heavy else None,
            data_refs=["/Category_spend"],
        )
    )

    cat_drift_flag = False
    drift_info = (input_data.insights or {}).get("category_drift") if input_data.insights else None
    if drift_info and "%" in drift_info:
        try:
            pct = float(drift_info.split(" ")[-1].replace("%", "")) / 100.0
            cat_drift_flag = pct >= 0.3
        except Exception:
            cat_drift_flag = False
    rule_triggers.append(
        RuleTrigger(
            rule_id="R-CAT-DRIFT-01",
            triggered=bool(cat_drift_flag),
            severity="medium" if cat_drift_flag else None,
            params={},
            reason="Category drift indicates >=30% rise" if cat_drift_flag else None,
            data_refs=["/insights/category_drift"],
        )
    )

    # Risk scoring per dimension
    def _risk_entry(dim: str, sev: str, summary: str, reasons: List[str], data_refs: List[str], contributors: List[Tuple[str, str]]):
        return RiskItem(
            id=f"RK-{dim.upper()}-01",
            dimension=dim,  # type: ignore
            score=_band_to_score(sev),
            severity=sev,  # type: ignore
            summary=summary,
            reasons=reasons,
            data_refs=data_refs,
            contributors=[{"rule_id": r, "severity": s} for r, s in contributors],
        )

    # deficit risk
    deficit_sev = "low"
    if r_deficit:
        deficit_sev = "high" if gap_pct_income > 0.15 else "medium" if gap_pct_income > 0.05 else "low"
    risks.append(
        _risk_entry(
            "deficit",
            deficit_sev,
            "Spending exceeds income this month" if r_deficit else "No current-month deficit detected",
            [
                f"Expenses exceed income by {gap_pct_income*100:.1f}% (₹{gap_amt:.0f})" if r_deficit else "",
            ],
            ["/current_month_expense", "/current_month_income"],
            [("R-DEFICIT-01", deficit_sev)] if r_deficit else [],
        )
    )

    # overspend risk
    if expense_delta_pct > 0:
        sev = _severity_from_ratio(expense_delta_pct)
        risks.append(
            _risk_entry(
                "overspend",
                sev,
                "Expenses are above average",
                [f"Current expenses {expense_delta_pct*100:.1f}% above average"],
                ["/current_month_expense", "/avg_monthly_expense"],
                [("R-OVRSPEND-01", sev)] if r_overspend else [],
            )
        )

    # savings discipline
    if r_save_low:
        sev = "high" if savings_rate < 0.1 else "medium"
        risks.append(
            _risk_entry(
                "savings",
                sev,
                "Savings rate below target",
                [f"Savings rate {savings_rate:.2f} below persona minimum {persona_min:.2f}"],
                ["/savings_rate"],
                [("R-SAVE-LOW-01", sev)],
            )
        )

    # volatility
    if r_vol_high:
        sev = "high" if income_vol > max(settings["volatility_high"] + 0.1, 0.35) else "medium"
        risks.append(
            _risk_entry(
                "volatility",
                sev,
                "Income volatility is elevated",
                [f"Volatility {income_vol:.2f} above threshold {settings['volatility_high']:.2f}"],
                ["/income_volatility"],
                [("R-VOL-INC-01", sev)],
            )
        )

    # stability
    if r_stab_low:
        sev = stab_sev
        risks.append(
            _risk_entry(
                "stability",
                sev,
                "Cashflow stability is low",
                [f"Stability {cashflow_stability:.2f} below 0.8"],
                ["/Behaviour_metrics/cashflow_stability"],
                [("R-STAB-LOW-01", sev)],
            )
        )

    # discretionary
    if r_disc_high:
        sev = disc_sev
        risks.append(
            _risk_entry(
                "discretionary",
                sev,
                "Discretionary spend share is high",
                [f"Discretionary ratio {discretionary_ratio:.2f} above 0.35"],
                ["/Behaviour_metrics/discretionary_ratio"],
                [("R-DISC-HIGH-01", sev)],
            )
        )

    # category outlier
    cat_contribs: List[Tuple[str, str]] = []
    if r_top_heavy:
        cat_contribs.append(("R-TOP-CAT-HEAVY-01", "medium"))
    if cat_drift_flag:
        cat_contribs.append(("R-CAT-DRIFT-01", "medium"))
    if cat_contribs:
        risks.append(
            _risk_entry(
                "category_outlier",
                "medium",
                "One or more categories are unusually heavy",
                [
                    f"{top_cat} accounts for {top_share*100:.1f}% of spend" if r_top_heavy else "",
                    (input_data.insights or {}).get("category_drift", "") if cat_drift_flag else "",
                ],
                ["/Category_spend", "/insights/category_drift"],
                cat_contribs,
            )
        )

    # Aggregate score (weighted)
    dim_scores: Dict[str, int] = {rk.dimension: rk.score for rk in risks}
    agg = 0.0
    for dim, w in weights.items():
        agg += float(dim_scores.get(dim, 0)) * float(w)

    # confidence scaling
    gamma = min(max(conf, 0.0), 1.0)
    agg *= gamma
    agg_sev = _aggregate_severity(agg)

    # Recommendations (selected subset)
    # REC-BALANCE-01 for deficit
    if r_deficit and cur_exp > 0:
        p = max(0.1, min(0.2, gap_amt / cur_exp))
        cut_pct = round(p, 2)
        cut_amt = round(cur_exp * cut_pct, 2)
        recs.append(
            Recommendation(
                id="REC-BALANCE-01",
                title="Close this month's gap by trimming discretionary spend",
                body=(
                    f"Because expenses (₹{cur_exp:.0f}) exceed income (₹{cur_inc:.0f}) by "
                    f"{gap_pct_income*100:.1f}%, reduce discretionary categories by {cut_pct*100:.0f}% (≈ ₹{cut_amt:.0f})."
                ),
                actions=[
                    "Lower discretionary caps by the suggested percent",
                    "Pause non-essential subscriptions for 30 days",
                ],
                amounts={"target_cut_pct": cut_pct, "cut_amount": cut_amt},
                linked_risks=["RK-DEFICIT-01"],
                priority=1,
                valid_for_days=30,
                data_refs=["/current_month_expense", "/current_month_income"],
            )
        )

    # REC-SAVE-BOOST-01 for savings
    if r_save_low and avg_exp > 0:
        target_rate = max(savings_rate, persona_min)
        target_amt = round(target_rate * avg_inc, 2)
        recs.append(
            Recommendation(
                id="REC-SAVE-BOOST-01",
                title="Boost savings rate to persona minimum",
                body=(
                    f"Because savings_rate ({savings_rate:.2f}) < persona minimum ({persona_min:.2f}), "
                    f"set an automated transfer of ₹{target_amt:.0f} on income receipt."
                ),
                actions=["Set auto-transfer on payday", "Track weekly savings progress"],
                amounts={"new_savings_rate": target_rate, "suggested_monthly_saving": target_amt},
                linked_risks=["RK-SAVINGS-01"],
                priority=2,
                valid_for_days=90,
                data_refs=["/savings_rate"],
            )
        )

    # REC-BUFFER-01 for volatility
    if r_vol_high and avg_exp > 0:
        n_months = 6 if persona == "gig_worker" else 3
        buffer_target = round(n_months * avg_exp, 2)
        recs.append(
            Recommendation(
                id="REC-BUFFER-01",
                title="Build an income buffer",
                body=(
                    f"Income volatility ({income_vol:.2f}) > threshold ({settings['volatility_high']:.2f}). "
                    f"Target a buffer of ₹{buffer_target:.0f} (≈ {n_months} months of expenses)."
                ),
                actions=["Create buffer sub-account", "Auto-sweep surplus weekly"],
                amounts={"buffer_target": buffer_target},
                linked_risks=["RK-VOLATILITY-01"],
                priority=2,
                valid_for_days=180,
                data_refs=["/income_volatility", "/avg_monthly_expense"],
            )
        )

    # REC-CAP-01 for overspend
    if r_overspend and avg_exp > 0:
        cap = round(avg_exp * 1.05, 2)
        recs.append(
            Recommendation(
                id="REC-CAP-01",
                title="Set a spending cap",
                body=(
                    f"Current expenses are {expense_delta_pct*100:.1f}% above average. Cap next month at ₹{cap:.0f}."
                ),
                actions=["Enable monthly cap alerts", "Allocate caps to top discretionary categories"],
                amounts={"monthly_cap": cap},
                linked_risks=["RK-OVERSPEND-01"],
                priority=3,
                valid_for_days=30,
                data_refs=["/current_month_expense", "/avg_monthly_expense"],
            )
        )

    # Build action plan (lightweight)
    plan = ActionPlan(
        next_30_days=[
            {
                "action_id": "ACT-TRIM-01",
                "title": "Trim discretionary spend by suggested percent",
                "kpi": "Discretionary reduction %",
                "target": "≥ 10%",
            },
            {
                "action_id": "ACT-AUTO-SAVE-01",
                "title": "Set up automated savings transfer",
                "kpi": "Monthly saved",
                "target": "= suggested",
            },
        ],
        next_90_days=[
            {
                "action_id": "ACT-BUFFER-01",
                "title": "Build/maintain buffer",
                "kpi": "Buffer months",
                "target": "3–6 months",
            }
        ],
        kpis=[
            {"name": "Net cashflow", "baseline": f"₹{net:.0f}", "target": "> 0"},
            {"name": "Savings rate", "baseline": f"{savings_rate:.2f}", "target": f">= {persona_min:.2f}"},
        ],
    )

    output = OutputPayload(
        metadata={
            "user_id": input_data.user_id,
            "month": input_data.month,
            "persona": input_data.persona_type or "",
            "currency": currency,
            "generated_at": now_iso,
            "engine_version": ENGINE_VERSION,
            "confidence": f"{conf:.2f}",
            "valid_until": f"{input_data.month}-28",  # simplified EOM
        },
        risks=risks,
        rule_triggers=rule_triggers,
        recommendations=recs,
        action_plan=plan,
        alerts=[],
        audit={
            "input_fields_present": list(input_data.model_dump(exclude_none=True).keys()),
            "ruleset_version": RULESET_VERSION,
        },
    )

    return output
