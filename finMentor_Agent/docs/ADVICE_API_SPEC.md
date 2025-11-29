# Advice Generator API Specification

## Endpoint
```
POST http://localhost:8001/advice/generate
```

## Purpose
Generate personalized financial advice that **directly answers the user's specific question** while considering their financial snapshot, risk analysis, and behavioral patterns.

---

## Request Payload

### Required Fields

```json
{
  "user_id": "string",
  "rules_output": {
    "risk_summary": {
      "triggered_rules": [],
      "risk_level": "string",
      "risk_score": 0,
      "recommendations": []
    },
    "normalized_data": {
      "avg_monthly_income": 0,
      "avg_monthly_expense": 0,
      "current_month_income": 0,
      "current_month_expense": 0,
      "savings_rate": 0.0,
      "income_volatility": 0.0
    }
  },
  "behavior_output": {
    "user_id": "string",
    "behavior_flags": [],
    "behavior_score": 0,
    "risk_level": "string"
  },
  "persona_type": "gig_worker" | "salaried" | "default",
  "user_query": "string or null"  // ⚠️ THIS IS CRITICAL!
}
```

---

## The user_query Field

### ⚠️ **CRITICAL REQUIREMENT**

The `user_query` field contains the **user's specific financial question** that MUST be answered directly in the advice response.

### Examples:

| user_query | Expected Advice Should Include |
|------------|-------------------------------|
| `"Can I go on a vacation?"` | Direct answer: "Based on your current financial situation with only ₹12,000 savings and ₹45,000 debt, a vacation is **not recommended** right now. However, if you must travel, consider a budget trip under ₹5,000 after saving for 2 more months." |
| `"Should I buy a new phone?"` | "With your current emergency fund at only 0.22 months, purchasing a new phone is **not advisable**. Focus on building your emergency fund to at least ₹96,000 (2 months expenses) first. If your phone is essential for your gig work, consider a budget option under ₹15,000." |
| `"How much should I save monthly?"` | "Based on your ₹55,000 monthly income, you should save **₹11,000 per month** (20% savings rate). Currently you're saving only ₹7,150 (13%), which is below the target for gig workers." |
| `null` or not provided | Provide general financial health assessment and improvement recommendations. |

---

## LLM Prompt Template for Advice API

Your advice generation API should use an LLM with a prompt like this:

```python
# Extract spending categories from rules_output if available
spending_breakdown = ""
if 'normalized_data' in rules_output and 'spending_categories' in rules_output['normalized_data']:
    categories = rules_output['normalized_data']['spending_categories']
    spending_breakdown = "\n".join([f"  - {cat['category']}: ₹{cat['amount']:,.0f} ({cat['percentage']:.1f}%)" 
                                     for cat in categories])

system_prompt = f"""
You are a financial advisor for {persona_type} users in India.

USER QUESTION: "{user_query or 'No specific question - provide general advice'}"

FINANCIAL CONTEXT:
- Monthly Income: ₹{normalized_data['avg_monthly_income']:,.0f}
- Monthly Expenses: ₹{normalized_data['avg_monthly_expense']:,.0f}
- Savings Rate: {normalized_data['savings_rate'] * 100:.1f}%
- Income Stability: {100 - normalized_data['income_volatility'] * 100:.0f}%
- Risk Level: {behavior_output['risk_level']}
- Behavior Flags: {', '.join(behavior_output['behavior_flags'])}

SPENDING BREAKDOWN:
{spending_breakdown if spending_breakdown else "Not available"}

DETECTED RISKS:
{format_risks(rules_output)}

CRITICAL INSTRUCTIONS:
1. **ALWAYS answer the user's question FIRST and DIRECTLY** if user_query is provided
2. Use ACTUAL numbers from the data above (e.g., Food: ₹12,000, not ₹0)
3. Never make up or hallucinate spending amounts
4. Provide specific, actionable advice with real numbers
5. Consider their {persona_type} persona (irregular income if gig_worker)
6. Be empathetic but honest about financial risks

Response format:
- Summary: Direct answer to their question + financial health overview (use REAL data)
- Action Steps: Prioritized concrete actions
- Tips: Specific savings/spending/stability recommendations
"""

user_prompt = f"Answer the user's question: '{user_query}'" if user_query else "Provide general financial advice"
```

**CRITICAL: Pass spending_categories to normalized_data**

In your LangGraph agent (or in advice API), ensure `normalized_data` includes spending breakdown:

```python
# In your advice API or LangGraph transformation
normalized_data = {
    "avg_monthly_income": income_data.get("average_monthly", 0),
    "avg_monthly_expense": spending_data.get("total_monthly", 0),
    "savings_rate": savings_data.get("monthly_savings_rate", 0),
    "income_volatility": (100 - income_data.get("stability_score", 50)) / 100.0,
    "spending_categories": spending_data.get("categories", [])  # ADD THIS!
}
```

---

## Response Format

### Current Response (Working ✅)
```json
{
  "user_id": "GIG_001",
  "summary": "string - MUST answer user_query first if provided",
  "top_risks": ["risk1", "risk2"],
  "behavioral_warnings": ["warning1", "warning2"],
  "action_steps": [
    {
      "title": "string",
      "description": "string",
      "priority": "high" | "medium" | "low"
    }
  ],
  "savings_tip": "string",
  "spending_tip": "string",
  "stability_tip": "string",
  "confidence_message": "string",
  "generated_at": "ISO8601 timestamp"
}
```

### Example Response for "Can I go on a vacation?"

```json
{
  "user_id": "GIG_001",
  "summary": "❌ A vacation is NOT recommended right now. With only ₹12,000 in savings (0.22 months emergency fund) and ₹45,000 in debt, you lack the financial buffer for discretionary travel. However, if travel is essential, consider a low-cost staycation or budget trip under ₹3,000 after building your emergency fund to at least ₹48,000 (1 month's expenses).",
  
  "top_risks": [
    "insufficient_emergency_fund",
    "high_debt_burden",
    "unstable_cashflow"
  ],
  
  "action_steps": [
    {
      "title": "FIRST: Build Emergency Fund to ₹48,000",
      "description": "Before ANY discretionary spending (including vacations), save 1 month's expenses. Set aside ₹9,000/month for 4 months.",
      "priority": "high"
    },
    {
      "title": "Pay Down High-Interest Debt",
      "description": "Focus on credit card debt first. Allocate ₹5,000/month towards debt repayment.",
      "priority": "high"
    },
    {
      "title": "Plan Low-Cost Recreation",
      "description": "If you need a break, consider free/low-cost local activities like parks, museums, or day trips under ₹500.",
      "priority": "medium"
    }
  ],
  
  "savings_tip": "Save ₹11,000/month (20% of income) - ₹9,000 for emergency fund + ₹2,000 for future vacation fund. Once emergency fund is complete, save for vacation separately.",
  
  "spending_tip": "Reduce discretionary spending (currently 31%) to 20% by cutting entertainment budget from ₹5,000 to ₹2,000. Use savings for emergency fund.",
  
  "stability_tip": "Diversify your gig income streams. Your current stability score of 42/100 is risky. Add 1-2 more reliable income sources.",
  
  "confidence_message": "Based on your provided data, this advice is 95% confident. A vacation would risk your financial stability given current debt and savings levels.",
  
  "generated_at": "2025-11-29T06:35:00Z"
}
```

---

## Implementation Checklist for Backend Team

### ✅ Already Working
- [x] API accepts all required fields
- [x] Returns properly structured response
- [x] Handles gig_worker persona

### ⚠️ Needs Implementation
- [ ] **Extract and prioritize `user_query` field from request**
- [ ] **Update LLM system prompt to answer user_query FIRST**
- [ ] **Include user_query in LLM context**
- [ ] **Validate summary field directly addresses the question**
- [ ] **Test with various user questions** (vacation, purchase decisions, savings goals)

---

## Testing

### Test Case 1: Vacation Question
```bash
curl -X POST http://localhost:8001/advice/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "GIG_001",
    "user_query": "Can I go on a vacation?",
    "rules_output": {...},
    "behavior_output": {...},
    "persona_type": "gig_worker"
  }'
```

**Expected**: Summary should start with "A vacation is NOT recommended..." or "You can afford a small vacation if..."

### Test Case 2: No Query (General Advice)
```bash
curl -X POST http://localhost:8001/advice/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "GIG_001",
    "user_query": null,
    "rules_output": {...},
    "behavior_output": {...},
    "persona_type": "gig_worker"
  }'
```

**Expected**: General financial health assessment without specific question answer.

---

## Common Issues

### ❌ Problem: Generic advice ignoring user question
```json
{
  "summary": "Your financial health is at risk due to unstable cash flow..."
}
```
This doesn't answer "Can I go on a vacation?"

### ✅ Solution: Question-focused advice
```json
{
  "summary": "Regarding your vacation question: Not recommended right now due to low savings (₹12,000) and high debt (₹45,000). Build ₹48,000 emergency fund first..."
}
```

---

## Priority
🔥 **CRITICAL** - This is the core user experience. Users expect their specific questions to be answered, not just generic advice.

## Next Steps
1. Update your advice API to extract `user_query` from payload
2. Modify LLM prompt to prioritize answering the user's question
3. Test with the example queries above
4. Ensure `summary` field always addresses the user_query when provided
