from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from .models import NormalizedInput, RiskItem, RuleTrigger, Recommendation
from .config import DEFAULTS, persona_value

logger = logging.getLogger(__name__)


def _fmt_pct(x: float) -> int:
    """Format float as percentage (e.g., 0.25 → 25)"""
    try:
        return int(round(x * 100))
    except Exception:
        return 0


def _fmt_currency(amount: float) -> str:
    """Format amount with currency symbol"""
    try:
        return f"{DEFAULTS['currency']}{int(round(amount))}"
    except Exception:
        return f"{DEFAULTS['currency']}0"


def _calculate_smart_cap(current_spend: float, income: float, target_ratio: float) -> float:
    """
    Calculate smart spending cap based on current behavior.
    Makes recommendation feel AI-like with dynamic calculation.
    
    For REDUCTION rules: Ensures target is ALWAYS below current spend
    to produce positive savings (Fixes LOGIC-01, LOGIC-02).
    
    Returns MINIMUM of:
    - Current spend (ceiling)
    - MAX(80% of current, target_ratio × income)
    
    This ensures: target < current (positive savings) AND target is achievable.
    """
    target_from_income = income * target_ratio
    gradual_reduction = current_spend * 0.8
    
    # Take the more achievable target (higher of the two)
    achievable_target = max(target_from_income, gradual_reduction)
    
    # But never exceed current spend (must be a reduction)
    return min(current_spend, achievable_target)


def build_recommendations(data: NormalizedInput, risks: List[RiskItem], rules: List[RuleTrigger]) -> List[Recommendation]:
    """
    Build personalized recommendations with dynamic parameter injection.
    
    Maps triggered rules to actionable recommendations with:
    - Smart calculations (e.g., temp_cap = current_spend × 0.8)
    - Persona-aware suggestions
    - Dynamic amounts that feel "AI-like"
    """
    recs: List[Recommendation] = []
    risk_index = {r.dimension: r for r in risks}
    rule_index = {r.rule_id: r for r in rules}
    
    logger.info(f"Building recommendations from {len(rules)} triggered rules")

    # From deficit
    r_def = rule_index.get("R-DEFICIT-01")
    if r_def and r_def.triggered:
        gap = r_def.params.get("gap_amt", 0.0)
        cut_pct = min(0.20, max(0.10, gap / max(data.current_month_expense, 1e-6)))
        title = "Close this month's gap"
        body = (
            f"You're short by {DEFAULTS['currency']}{int(gap)} this month. Reduce discretionary spend by "
            f"{_fmt_pct(cut_pct)}% across top categories to balance."
        )
        recs.append(
            Recommendation(
                id="REC-BALANCE-01",
                title=title,
                body=body,
                actions=[
                    "Set weekly discretionary budget envelopes",
                    "Pause non-essential subscriptions until balance is restored",
                ],
                amounts={"target_cut_pct": cut_pct},
                linked_risks=[risk_index["deficit"].id] if "deficit" in risk_index else [],
                priority=1,
                data_refs=["/current_month_expense", "/current_month_income"],
            )
        )

    # Savings rate low
    r_save = rule_index.get("R-SAVE-LOW-01")
    if r_save and r_save.triggered:
        target = r_save.params.get("target_rate")
        title = "Boost savings rate"
        body = (
            f"Savings rate is below target. Set an auto-transfer to reach {_fmt_pct(target)}% upon income receipt."
        )
        recs.append(
            Recommendation(
                id="REC-SAVE-BOOST-01",
                title=title,
                body=body,
                actions=["Create automated savings transfer on payday"],
                amounts={"new_savings_rate": target},
                linked_risks=[risk_index["savings"].id] if "savings" in risk_index else [],
                priority=2,
                data_refs=["/savings_rate"],
            )
        )

    # Volatility high
    r_vol = rule_index.get("R-VOL-INC-01")
    if r_vol and r_vol.triggered:
        persona = data.persona_type or "default"
        N = 6 if persona == "gig_worker" else 3
        buf_target = N * data.avg_monthly_expense
        recs.append(
            Recommendation(
                id="REC-BUFFER-01",
                title="Build income buffer",
                body=f"Income volatility is elevated. Build a {N}-month buffer of {DEFAULTS['currency']}{int(buf_target)}.",
                actions=["Allocate a buffer sub-account", "Divert surplus to buffer until target reached"],
                amounts={"buffer_target": buf_target, "months": N},
                linked_risks=[risk_index["volatility"].id] if "volatility" in risk_index else [],
                priority=1,
                data_refs=["/income_volatility"],
            )
        )

    # Overspend
    r_ovr = rule_index.get("R-OVRSPEND-01")
    if r_ovr and r_ovr.triggered:
        cap = data.avg_monthly_expense * 1.05
        recs.append(
            Recommendation(
                id="REC-CAP-01",
                title="Set monthly cap",
                body=f"Expenses exceed average. Set a soft cap at {DEFAULTS['currency']}{int(cap)} (≈105% of average).",
                actions=["Enable monthly cap alerts", "Lock discretionary spend after cap"],
                amounts={"cap_amount": cap},
                linked_risks=[risk_index["overspend"].id] if "overspend" in risk_index else [],
                priority=2,
                data_refs=["/avg_monthly_expense", "/current_month_expense"],
            )
        )

    # Category drift - Enhanced with smart cap calculation
    r_drift = rule_index.get("R-CAT-DRIFT-01")
    if r_drift and r_drift.triggered:
        cat = r_drift.params.get("category")
        if not cat:
            logger.warning("R-CAT-DRIFT-01 triggered but no category in params")
        else:
            current_spend = data.category_spend.get(cat, 0.0)
            income = data.current_month_income or data.avg_monthly_income
            
            # Smart cap: Use _calculate_smart_cap with target ratio from config
            category_target = DEFAULTS.get("category_thresholds", {}).get(cat.lower(), 0.15)
            temp_cap = _calculate_smart_cap(current_spend, income, category_target)
            reduction_pct = ((current_spend - temp_cap) / current_spend * 100) if current_spend > 0 else 0
            
            recs.append(
                Recommendation(
                    id="REC-CAT-AUDIT-01",
                    title=f"Audit category: {cat}",
                    body=f"{cat} spending jumped recently to {_fmt_currency(current_spend)}. Run a 1-week audit and reduce to {_fmt_currency(temp_cap)} ({reduction_pct:.0f}% reduction).",
                    actions=[
                        "Review last 10 transactions in " + cat,
                        f"Set temporary cap at {_fmt_currency(temp_cap)}",
                        "Identify recurring charges that can be cancelled"
                    ],
                    amounts={"category": cat, "temp_cap": temp_cap, "reduction_pct": reduction_pct},
                    linked_risks=[risk_index["category_outlier"].id] if "category_outlier" in risk_index else [],
                    priority=3,
                    data_refs=[f"/category_spend/{cat}"],
                )
            )

    # Discretionary ratio high or HSD - Enhanced with daily budget calculation
    r_disc = rule_index.get("R-DISC-HIGH-01")
    r_hsd = rule_index.get("R-HSD-01")
    if (r_disc and r_disc.triggered) or (r_hsd and r_hsd.triggered):
        income = data.current_month_income or data.avg_monthly_income
        # Estimate essential as 65% of income (rough approximation)
        essential = income * 0.65
        available_for_discretionary = income - essential
        target_discretionary = available_for_discretionary * 0.6  # 60% of available funds
        daily_budget = target_discretionary / 30  # Rough daily allowance
        
        recs.append(
            Recommendation(
                id="REC-SPEND-ALERT-01",
                title="Tighten daily spending",
                body=f"Discretionary spending is high. Set a daily budget of {_fmt_currency(daily_budget)} and enable alerts when you hit 80% of daily limit.",
                actions=[
                    f"Enable daily alerts at {_fmt_currency(daily_budget * 0.8)} (80% of daily budget)",
                    "Apply hard stops after daily budget is exceeded",
                    "Use cash envelopes for discretionary categories"
                ],
                amounts={"daily_budget": daily_budget, "monthly_target": target_discretionary},
                linked_risks=[risk_index["discretionary"].id] if "discretionary" in risk_index else [],
                priority=3,
                data_refs=["/behavior_metrics/discretionary_ratio"],
            )
        )

    # Emergency fund low - Enhanced with timeline calculation
    r_emerg = rule_index.get("R-EMERG-FUND-01")
    if r_emerg and r_emerg.triggered:
        required = r_emerg.params.get("required_fund", 0)
        shortfall = r_emerg.params.get("shortfall", 0)
        income = data.current_month_income or data.avg_monthly_income
        
        # Smart calculation: 10% monthly allocation with timeline
        monthly_allocation = income * 0.10
        months_to_target = int(shortfall / monthly_allocation) if monthly_allocation > 0 else 0
        
        recs.append(
            Recommendation(
                id="REC-EMERG-FUND-01",
                title="Build emergency fund",
                body=f"Your emergency fund is {_fmt_currency(shortfall)} short of the recommended {_fmt_currency(required)}. Allocate {_fmt_currency(monthly_allocation)} monthly (10% of income) to reach target in ~{months_to_target} months.",
                actions=[
                    f"Set up auto-transfer of {_fmt_currency(monthly_allocation)} on payday",
                    "Allocate all windfalls to emergency fund",
                    "Review and increase allocation after 3 months"
                ],
                amounts={"required_fund": required, "shortfall": shortfall, "monthly_allocation": monthly_allocation, "months_to_target": months_to_target},
                linked_risks=[risk_index["savings"].id] if "savings" in risk_index else [],
                priority=1,
                data_refs=["/emergency_fund_balance"],
            )
        )

    # Rent too high
    r_rent = rule_index.get("R-RENT-HIGH-01")
    if r_rent and r_rent.triggered:
        rent_ratio = r_rent.params.get("rent_ratio", 0)
        recs.append(
            Recommendation(
                id="REC-RENT-REDUCE-01",
                title="Housing cost is too high",
                body=f"Housing takes up {rent_ratio*100:.1f}% of income (recommended: ≤35%). Consider relocating or finding a roommate.",
                actions=["Explore cheaper housing options", "Negotiate rent reduction", "Consider shared accommodation"],
                amounts={"current_rent_ratio": rent_ratio},
                linked_risks=[risk_index["overspend"].id] if "overspend" in risk_index else [],
                priority=2,
                data_refs=["/rent_or_housing"],
            )
        )

    # Consecutive deficits
    r_consec = rule_index.get("R-CONSEC-DEF-01")
    if r_consec and r_consec.triggered:
        months = r_consec.params.get("consecutive_months", 0)
        recs.append(
            Recommendation(
                id="REC-DEFICIT-STREAK-01",
                title="Break the deficit streak",
                body=f"You've been in deficit for {months} consecutive months. Urgent action needed to balance income and expenses.",
                actions=["Cut all non-essential expenses immediately", "Look for additional income sources", "Review all subscriptions and cancel unused ones"],
                amounts={"deficit_months": months},
                linked_risks=[risk_index["deficit"].id] if "deficit" in risk_index else [],
                priority=1,
                data_refs=["/consecutive_deficit_count"],
            )
        )

    # Income drop - Enhanced with adjusted budget calculation
    r_inc_drop = rule_index.get("R-INCOME-DROP-01")
    if r_inc_drop and r_inc_drop.triggered:
        drop_pct = r_inc_drop.params.get("drop_pct", 0)
        current_income = data.current_month_income or data.avg_monthly_income
        previous_income = data.previous_month_income or current_income
        income_loss = previous_income - current_income
        
        # Smart calculation: Adjusted discretionary budget = (current_income - essential) * 0.5
        essential = data.total_essential_expense or (current_income * 0.65)
        adjusted_discretionary = max((current_income - essential) * 0.5, 0)
        
        recs.append(
            Recommendation(
                id="REC-INCOME-DROP-01",
                title="Income dropped significantly",
                body=f"Your income dropped by {_fmt_currency(income_loss)} ({drop_pct*100:.0f}%) from last month. Reduce discretionary spending to {_fmt_currency(adjusted_discretionary)} until income stabilizes.",
                actions=[
                    "Scale down discretionary expenses by 50%",
                    f"Set temporary monthly budget at {_fmt_currency(adjusted_discretionary)} for non-essentials",
                    "Tap emergency fund if essential expenses can't be covered",
                    "Explore freelance/side gigs to supplement income"
                ],
                amounts={"drop_percentage": drop_pct, "income_loss": income_loss, "adjusted_discretionary": adjusted_discretionary},
                linked_risks=[risk_index["volatility"].id] if "volatility" in risk_index else [],
                priority=1,
                data_refs=["/previous_month_income", "/current_month_income"],
            )
        )

    # Loan EMI high - Enhanced with savings calculation
    r_loan = rule_index.get("R-LOAN-EMI-HIGH-01")
    if r_loan and r_loan.triggered:
        emi_ratio = r_loan.params.get("income_ratio", 0)
        income = data.current_month_income or data.avg_monthly_income
        current_emi = income * emi_ratio
        target_emi_ratio = 0.35  # Target: 35% of income
        target_emi = income * target_emi_ratio
        potential_savings = current_emi - target_emi
        
        recs.append(
            Recommendation(
                id="REC-LOAN-REFI-01",
                title="Loan EMI burden is high",
                body=f"Your loan EMI is {_fmt_currency(current_emi)} ({emi_ratio*100:.0f}% of income). Target: ≤40%. Refinancing could save {_fmt_currency(potential_savings)}/month if you reduce EMI to {emi_ratio*100:.0f}% → 35%.",
                actions=[
                    "Compare refinancing rates from 3+ lenders",
                    "Consolidate multiple loans to reduce interest",
                    "Negotiate with current lenders for rate reduction",
                    f"Target monthly EMI: {_fmt_currency(target_emi)} (35% of income)"
                ],
                amounts={"emi_ratio": emi_ratio, "current_emi": current_emi, "target_emi": target_emi, "potential_savings": potential_savings},
                linked_risks=[risk_index["category_outlier"].id] if "category_outlier" in risk_index else [],
                priority=2,
                data_refs=["/loan_emi_total"],
            )
        )

    # Forecasted surplus (positive recommendation) - Enhanced with allocation plan
    r_surplus = rule_index.get("R-FCAST-SURPLUS-01")
    if r_surplus and r_surplus.triggered:
        surplus = r_surplus.params.get("surplus_amount", 0)
        
        # Smart allocation: 50-30-20 split (savings, investment, reward)
        savings_allocation = surplus * 0.50
        investment_allocation = surplus * 0.30
        reward_allocation = surplus * 0.20
        
        recs.append(
            Recommendation(
                id="REC-SURPLUS-INVEST-01",
                title="Great news: Surplus expected!",
                body=f"Next month is forecasted to have a surplus of {_fmt_currency(surplus)}. Smart allocation: {_fmt_currency(savings_allocation)} to savings (50%), {_fmt_currency(investment_allocation)} to investment (30%), {_fmt_currency(reward_allocation)} as reward (20%).",
                actions=[
                    f"Auto-transfer {_fmt_currency(savings_allocation)} to emergency fund",
                    f"Invest {_fmt_currency(investment_allocation)} in SIP/mutual funds",
                    f"Reward yourself with {_fmt_currency(reward_allocation)} guilt-free spending",
                    "Review allocation after 3 months"
                ],
                amounts={
                    "surplus_amount": surplus,
                    "savings_allocation": savings_allocation,
                    "investment_allocation": investment_allocation,
                    "reward_allocation": reward_allocation
                },
                linked_risks=[],
                priority=4,
                data_refs=["/Forecast/predicted_income_next_month", "/Forecast/predicted_expense_next_month"],
            )
        )
    
    # ====================
    # ADDITIONAL CATEGORY-SPECIFIC RULES
    # ====================
    
    # Food spending high (R-FOOD-HIGH-01)
    r_food = rule_index.get("R-FOOD-HIGH-01")
    if r_food and r_food.triggered:
        food_spend = data.category_spend.get("Food", 0)
        income = data.current_month_income or data.avg_monthly_income
        food_ratio = r_food.params.get("food_ratio", food_spend / income if income > 0 else 0)
        target_food = _calculate_smart_cap(food_spend, income, 0.25)  # Target: 25% of income
        savings = food_spend - target_food
        
        recs.append(
            Recommendation(
                id="REC-FOOD-REDUCE-01",
                title="Food spending is above ideal range",
                body=f"Food spending at {_fmt_currency(food_spend)} ({food_ratio*100:.0f}% of income). Target: ≤25%. Reduce to {_fmt_currency(target_food)} to save {_fmt_currency(savings)}/month.",
                actions=[
                    "Plan meals weekly to reduce impulsive dining out",
                    "Cook in batches for 3-4 days",
                    f"Set food budget cap at {_fmt_currency(target_food)}",
                    "Cancel unused food delivery subscriptions"
                ],
                amounts={"current_food": food_spend, "target_food": target_food, "monthly_savings": savings},
                linked_risks=[risk_index["category_outlier"].id] if "category_outlier" in risk_index else [],
                priority=2,
                data_refs=["/category_spend/Food"],
            )
        )
    
    # Transport spending high (R-TRANSPORT-HIGH-01)
    r_transport = rule_index.get("R-TRANSPORT-HIGH-01")
    if r_transport and r_transport.triggered:
        transport_spend = data.category_spend.get("Transport", 0)
        income = data.current_month_income or data.avg_monthly_income
        transport_ratio = r_transport.params.get("transport_ratio", transport_spend / income if income > 0 else 0)
        target_transport = _calculate_smart_cap(transport_spend, income, 0.15)  # Target: 15% of income
        savings = transport_spend - target_transport
        
        recs.append(
            Recommendation(
                id="REC-TRANSPORT-REDUCE-01",
                title="Transport costs are elevated",
                body=f"Transport spending at {_fmt_currency(transport_spend)} ({transport_ratio*100:.0f}% of income). Target: ≤15%. Optimize to {_fmt_currency(target_transport)} to save {_fmt_currency(savings)}/month.",
                actions=[
                    "Use public transport instead of ride-sharing apps",
                    "Carpool with colleagues for work commute",
                    f"Set transport budget cap at {_fmt_currency(target_transport)}",
                    "Consider monthly passes for regular routes"
                ],
                amounts={"current_transport": transport_spend, "target_transport": target_transport, "monthly_savings": savings},
                linked_risks=[risk_index["category_outlier"].id] if "category_outlier" in risk_index else [],
                priority=2,
                data_refs=["/category_spend/Transport"],
            )
        )
    
    # Entertainment spending high (R-ENTERTAINMENT-HIGH-01)
    r_entertainment = rule_index.get("R-ENTERTAINMENT-HIGH-01")
    if r_entertainment and r_entertainment.triggered:
        entertainment_spend = data.category_spend.get("Entertainment", 0)
        income = data.current_month_income or data.avg_monthly_income
        entertainment_ratio = r_entertainment.params.get("entertainment_ratio", entertainment_spend / income if income > 0 else 0)
        target_entertainment = _calculate_smart_cap(entertainment_spend, income, 0.10)  # Target: 10% of income
        savings = entertainment_spend - target_entertainment
        
        recs.append(
            Recommendation(
                id="REC-ENTERTAINMENT-REDUCE-01",
                title="Entertainment spending is above recommended",
                body=f"Entertainment at {_fmt_currency(entertainment_spend)} ({entertainment_ratio*100:.0f}% of income). Target: ≤10%. Cut to {_fmt_currency(target_entertainment)} to save {_fmt_currency(savings)}/month.",
                actions=[
                    "Review and cancel unused streaming subscriptions",
                    "Look for free/low-cost entertainment alternatives",
                    f"Set entertainment budget at {_fmt_currency(target_entertainment)}",
                    "Limit expensive outings to 1-2 per month"
                ],
                amounts={"current_entertainment": entertainment_spend, "target_entertainment": target_entertainment, "monthly_savings": savings},
                linked_risks=[risk_index["discretionary"].id] if "discretionary" in risk_index else [],
                priority=3,
                data_refs=["/category_spend/Entertainment"],
            )
        )
    
    logger.info(f"Generated {len(recs)} recommendations")
    return recs


def build_action_plan(recs: List[Recommendation]) -> Dict[str, List[Dict]]:
    next_30: List[Dict] = []
    next_90: List[Dict] = []
    for r in recs:
        next_30.append(
            {
                "action_id": r.id,
                "title": r.title,
                "kpi": "complete_action",
                "target": 1,
                "owner": "user",
            }
        )
    return {"next_30_days": next_30, "next_90_days": next_90, "kpis": []}
