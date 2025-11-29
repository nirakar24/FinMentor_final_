# Smart Recommendations System

## Overview
The enhanced recommendation engine generates personalized, actionable recommendations with **dynamic parameter injection** that makes suggestions feel "AI-like" even though they're rule-based.

## Key Features

### 1. Dynamic Parameter Calculation
Instead of generic advice, recommendations include:
- **Specific amounts**: "₹161 daily budget" instead of "reduce spending"
- **Calculated targets**: "Reduce food to ₹5,750 (20% cut)" with actual numbers
- **Timeline estimates**: "Reach target in ~12 months"
- **Savings projections**: "Save ₹3,450/month by refinancing"

### 2. Smart Cap Calculation
```python
def _calculate_smart_cap(current_spend: float, income: float, target_ratio: float) -> float:
    """
    Calculate intelligent spending caps that are achievable.
    
    Returns the HIGHER of:
    - Gradual reduction: 80% of current spend
    - Target from income: income × target_ratio
    
    This ensures caps are challenging but realistic.
    """
```

**Example**:
- Current food spending: ₹8,400
- Income: ₹25,000
- Target ratio: 25% (₹6,250)
- **Gradual reduction**: ₹6,720 (80% of current)
- **Target**: ₹6,250
- **Result**: ₹6,720 (more achievable first step)

### 3. Enhanced Recommendation Types

#### A. Category Spending (Food, Transport, Entertainment)
**Trigger**: R-FOOD-HIGH-01, R-TRANSPORT-HIGH-01, R-ENTERTAINMENT-HIGH-01

**Smart Parameters**:
```python
current_spend = category_spend["Food"]
target_spend = _calculate_smart_cap(current_spend, income, 0.25)  # 25% target
monthly_savings = current_spend - target_spend
reduction_pct = (monthly_savings / current_spend) × 100
```

**Output**:
```
Food spending at ₹8,400 (33.6% of income). Target: ≤25%. 
Reduce to ₹6,720 (20% reduction) to save ₹1,680/month.

Actions:
- Plan meals weekly to reduce impulsive dining out
- Cook in batches for 3-4 days
- Set food budget cap at ₹6,720
- Cancel unused food delivery subscriptions
```

#### B. Daily Budget for Discretionary Spending
**Trigger**: R-DISC-HIGH-01, R-HSD-01

**Smart Parameters**:
```python
essential = income × 0.65  # Estimate essentials
available_for_discretionary = income - essential
target_discretionary = available_for_discretionary × 0.6
daily_budget = target_discretionary / 30
alert_threshold = daily_budget × 0.80  # 80% alert
```

**Output**:
```
Discretionary spending is high. Set a daily budget of ₹175 
and enable alerts when you hit 80% of daily limit.

Actions:
- Enable daily alerts at ₹140 (80% of daily budget)
- Apply hard stops after daily budget is exceeded
- Use cash envelopes for discretionary categories
```

#### C. Emergency Fund with Timeline
**Trigger**: R-EMERG-FUND-01

**Smart Parameters**:
```python
shortfall = required_fund - current_balance
monthly_allocation = income × 0.10  # 10% of income
months_to_target = shortfall / monthly_allocation
```

**Output**:
```
Your emergency fund is ₹18,000 short of the recommended ₹30,000. 
Allocate ₹2,500 monthly (10% of income) to reach target in ~7 months.

Actions:
- Set up auto-transfer of ₹2,500 on payday
- Allocate all windfalls to emergency fund
- Review and increase allocation after 3 months
```

#### D. Income Drop Response
**Trigger**: R-INCOME-DROP-01

**Smart Parameters**:
```python
income_loss = previous_income - current_income
essential = current_income × 0.65
adjusted_discretionary = (current_income - essential) × 0.5  # Cut 50%
drop_pct = (income_loss / previous_income) × 100
```

**Output**:
```
Your income dropped by ₹8,000 (32%) from last month. 
Reduce discretionary spending to ₹4,375 until income stabilizes.

Actions:
- Scale down discretionary expenses by 50%
- Set temporary monthly budget at ₹4,375 for non-essentials
- Tap emergency fund if essential expenses can't be covered
- Explore freelance/side gigs to supplement income
```

#### E. Loan EMI Refinancing
**Trigger**: R-LOAN-EMI-HIGH-01

**Smart Parameters**:
```python
current_emi = income × emi_ratio
target_emi_ratio = 0.35  # Target: 35% of income
target_emi = income × target_emi_ratio
potential_savings = current_emi - target_emi
```

**Output**:
```
Your loan EMI is ₹12,000 (48% of income). Target: ≤40%. 
Refinancing could save ₹3,250/month if you reduce EMI to 48% → 35%.

Actions:
- Compare refinancing rates from 3+ lenders
- Consolidate multiple loans to reduce interest
- Negotiate with current lenders for rate reduction
- Target monthly EMI: ₹8,750 (35% of income)
```

#### F. Surplus Allocation (Positive Recommendation)
**Trigger**: R-FCAST-SURPLUS-01

**Smart Parameters**:
```python
surplus = forecasted_surplus
savings_allocation = surplus × 0.50  # 50%
investment_allocation = surplus × 0.30  # 30%
reward_allocation = surplus × 0.20  # 20%
```

**Output**:
```
Next month is forecasted to have a surplus of ₹5,000. 
Smart allocation: ₹2,500 to savings (50%), ₹1,500 to investment (30%), 
₹1,000 as reward (20%).

Actions:
- Auto-transfer ₹2,500 to emergency fund
- Invest ₹1,500 in SIP/mutual funds
- Reward yourself with ₹1,000 guilt-free spending
- Review allocation after 3 months
```

## Helper Functions

### _fmt_currency(amount: float) -> str
```python
def _fmt_currency(amount: float) -> str:
    """Format amount with currency symbol from config."""
    return f"{DEFAULTS['currency']}{int(round(amount))}"
```

**Example**: `4200.5` → `"₹4200"`

### _calculate_smart_cap(current_spend, income, target_ratio)
See "Smart Cap Calculation" section above.

### _fmt_pct(x: float) -> int
```python
def _fmt_pct(x: float) -> int:
    """Format float as percentage."""
    return int(round(x * 100))
```

**Example**: `0.25` → `25`

## Configuration

Recommendation parameters are driven by thresholds in `engine/config.py`:

```python
DEFAULTS = {
    "category_thresholds": {
        "food": 0.30,        # Food should be <30% of expenses
        "transport": 0.20,   # Transport <20%
        "entertainment": 0.15,  # Entertainment <15%
        "utilities": 0.12,   # Utilities <12%
    },
    "emergency_fund_months": {
        "gig_worker": 6,     # 6 months for gig workers
        "salaried": 3,       # 3 months for salaried
    },
    "loan_emi_income_ratio_max": 0.40,  # EMI ≤40% of income
    "rent_income_ratio_max": 0.35,      # Rent ≤35% of income
    # ... more thresholds
}
```

## Rule-to-Recommendation Mapping

| Rule ID | Recommendation ID | Parameters Injected |
|---------|-------------------|---------------------|
| R-DEFICIT-01 | RC-DEFICIT-MANAGE-01 | deficit, target_reduction |
| R-SAVE-LOW-01 | REC-SAVE-BOOST-01 | target_rate |
| R-VOL-INC-01 | REC-BUFFER-01 | buffer_target, months |
| R-DISC-HIGH-01, R-HSD-01 | REC-SPEND-ALERT-01 | daily_budget, alert_threshold |
| R-CAT-DRIFT-01 | REC-CAT-AUDIT-01 | temp_cap, reduction_pct |
| R-EMERG-FUND-01 | REC-EMERG-FUND-01 | monthly_allocation, months_to_target |
| R-RENT-HIGH-01 | REC-RENT-REDUCE-01 | rent_ratio |
| R-CONSEC-DEF-01 | REC-DEFICIT-STREAK-01 | deficit_months |
| R-INCOME-DROP-01 | REC-INCOME-DROP-01 | income_loss, adjusted_discretionary |
| R-LOAN-EMI-HIGH-01 | REC-LOAN-REFI-01 | potential_savings, target_emi |
| R-FCAST-SURPLUS-01 | REC-SURPLUS-INVEST-01 | savings/investment/reward allocations |
| R-FOOD-HIGH-01 | REC-FOOD-REDUCE-01 | target_food, monthly_savings |
| R-TRANSPORT-HIGH-01 | REC-TRANSPORT-REDUCE-01 | target_transport, monthly_savings |
| R-ENTERTAINMENT-HIGH-01 | REC-ENTERTAINMENT-REDUCE-01 | target_entertainment, monthly_savings |

## Why This Feels "AI-Like"

Even though recommendations are rule-based, they feel intelligent because:

1. **Context-Aware Numbers**: "₹6,720" is specific to your situation (not generic "reduce spending")
2. **Personalized Timelines**: "~7 months to target" shows planning
3. **Achievable Steps**: 80% of current (not jumping to ideal immediately)
4. **Multiple Perspectives**: Shows current, target, savings, percentage all together
5. **Persona-Specific**: Gig workers get 6-month buffer, salaried get 3-month
6. **Dynamic Thresholds**: Food cap depends on your actual spending pattern

## Example Output

```json
{
  "id": "REC-FOOD-REDUCE-01",
  "title": "Food spending is above ideal range",
  "body": "Food spending at ₹8,400 (33.6% of income). Target: ≤25%. Reduce to ₹6,720 (20% reduction) to save ₹1,680/month.",
  "actions": [
    "Plan meals weekly to reduce impulsive dining out",
    "Cook in batches for 3-4 days",
    "Set food budget cap at ₹6,720",
    "Cancel unused food delivery subscriptions"
  ],
  "amounts": {
    "current_food": 8400.0,
    "target_food": 6720.0,
    "monthly_savings": 1680.0
  },
  "linked_risks": ["RK-CATEGORY_OUTLIER"],
  "priority": 2
}
```

## Testing

Test with sample data:
```bash
python scripts/run_sample.py
```

View recommendations:
```bash
python scripts/run_sample.py | jq '.recommendations'
```

## Future Enhancements

1. **Historical Trend Analysis**: "You've reduced food spending 15% over 3 months"
2. **Peer Benchmarking**: "Similar gig workers spend 20% less on transport"
3. **Seasonal Adjustments**: "Food spending typically increases 10% in December"
4. **Goal Tracking**: "You're 60% of the way to your emergency fund goal"
5. **Success Predictions**: "Based on past behavior, 75% chance you'll hit this target"
6. **Alternative Scenarios**: "If you reduce food by 20%, you could save ₹1,680/month"

## Related Documentation

- `DYNAMIC_RULES_GUIDE.md` - Dynamic rule loading system
- `WEIGHTED_RISK_SCORING.md` - Weighted risk calculation
- `engine/config.py` - Threshold configuration
- `engine/recommendations.py` - Implementation

---

**Last Updated**: 2025-11-24  
**Version**: 1.0.0
