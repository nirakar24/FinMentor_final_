# API Specifications for Financial Coaching Agent

## Overview
This document specifies the expected request/response formats for all backend APIs that integrate with the LangGraph agent.

---

## 1. Snapshot API

**Endpoint:** `GET /snapshot/{user_id}`

**Response Format:**
```json
{
  "user_id": "string",
  "profile": {
    "name": "string",
    "persona": "gig_worker | salaried | default",
    "age": 28,
    "location": "string"
  },
  "income": {
    "monthly_streams": [...],
    "average_monthly": 55000,
    "stability_score": 42
  },
  "spending": {
    "total_monthly": 48000,
    "categories": [...],
    "discretionary_ratio": 0.31
  },
  "savings": {
    "current_balance": 12000,
    "emergency_fund_months": 0.22,
    "monthly_savings_rate": 0.13
  },
  "debt": {
    "total_outstanding": 45000,
    "monthly_emi": 3500,
    "types": [...]
  },
  "financial_health_score": 38,
  "alerts": [...],
  "timestamp": "ISO-8601"
}
```

---

## 2. Rule Engine API

**Endpoint:** `POST /evaluate`

**Request Format:**
```json
{
  "user_id": "GIG_001",
  "month": "2025-11",
  "avg_monthly_income": 55000,
  "avg_monthly_expense": 48000,
  "current_month_income": 55000,
  "current_month_expense": 48000
}
```

**Response Format:**
```json
{
  "metadata": {...},
  "risks": [...],
  "rule_triggers": [...],
  "recommendations": [...],
  "action_plan": {...},
  "alerts": [],
  "audit": {...}
}
```

---

## 3. Behavior Detection API

**Endpoint:** `POST /behavior/detect`

**Request Format:**
```json
{
  "user_id": "GIG_001",
  "avg_daily_expense": 1600.0,
  "high_spend_days": 0,
  "cashflow_stability": 0.0,
  "discretionary_ratio": 0.31
}
```

**Response Format:**
```json
{
  "user_id": "GIG_001",
  "behavior_flags": ["high_discretionary_spender", "unstable_cashflow"],
  "behavior_score": 40,
  "risk_level": "low | medium | high",
  "generated_at": "ISO-8601"
}
```

---

## 4. Advice Generation API ⚠️ **CRITICAL UPDATE NEEDED**

**Endpoint:** `POST /advice/generate`

**Request Format:**
```json
{
  "user_id": "GIG_001",
  "rules_output": {
    "metadata": {...},
    "risks": [...],
    "recommendations": [...],
    "risk_summary": {
      "triggered_rules": [],
      "risk_level": "string",
      "risk_score": 0,
      "recommendations": []
    },
    "normalized_data": {
      "avg_monthly_income": 55000,
      "avg_monthly_expense": 48000,
      "current_month_income": 55000,
      "current_month_expense": 48000,
      "savings_rate": 0.13,
      "income_volatility": 0.58
    }
  },
  "behavior_output": {
    "user_id": "GIG_001",
    "behavior_flags": [...],
    "behavior_score": 40,
    "risk_level": "medium"
  },
  "persona_type": "gig_worker | salaried | default",
  "user_query": "Can I go on a vacation?"  // ⚠️ NEW FIELD - User's specific question
}
```

### **IMPORTANT: How to Handle `user_query`**

The LLM prompt in your advice API should be updated to:

1. **Check if `user_query` exists and is not null/empty**
2. **If user_query is provided:**
   - Answer the specific question FIRST
   - Use the financial context (rules_output, behavior_output) to provide a personalized answer
   - Then provide general financial advice

3. **If user_query is NOT provided:**
   - Return general financial advice as you currently do

### **Example LLM Prompt Structure:**

```python
user_query = request.get("user_query")

if user_query:
    prompt = f"""
You are a financial advisor for a {persona_type} user.

USER'S QUESTION: "{user_query}"

FINANCIAL CONTEXT:
- Monthly Income: ₹{normalized_data['avg_monthly_income']}
- Monthly Expenses: ₹{normalized_data['avg_monthly_expense']}
- Savings Rate: {normalized_data['savings_rate']*100}%
- Emergency Fund: {emergency_fund_months} months
- Debt: ₹{debt_outstanding}
- Risk Level: {behavior_output['risk_level']}
- Behavior Flags: {behavior_output['behavior_flags']}

DETECTED RISKS:
{risks_summary}

INSTRUCTIONS:
1. Answer the user's question DIRECTLY and SPECIFICALLY
2. Consider their current financial situation
3. Be honest - if it's financially risky, say so
4. Provide alternatives or conditions if applicable
5. Then provide general advice for improvement

Respond in a helpful, empathetic tone.
"""
else:
    prompt = """
    [Your existing general advice prompt]
    """
```

### **Example Response for "Can I go on a vacation?":**

```json
{
  "user_id": "GIG_001",
  "summary": "❌ A vacation is NOT recommended right now. With only 0.22 months of emergency savings (₹12,000) and ₹45,000 in debt, you lack a financial safety net. However, if you must take a break, consider a budget staycation under ₹3,000.",
  "top_risks": ["unstable_cashflow", "no_emergency_fund", "high_debt"],
  "action_steps": [
    {
      "title": "Build Emergency Fund FIRST",
      "description": "Save at least ₹96,000 (2 months expenses) before discretionary spending like vacations",
      "priority": "critical"
    },
    {
      "title": "Reduce Debt Before Luxuries",
      "description": "Pay down your ₹45,000 debt to free up cash flow",
      "priority": "high"
    },
    {
      "title": "Alternative: Budget Staycation",
      "description": "If you need rest, explore local attractions or take a day trip under ₹3,000",
      "priority": "medium"
    }
  ],
  "savings_tip": "Save ₹11,000/month (20% of income) to build emergency fund in 9 months",
  "spending_tip": "Pause discretionary spending like vacations until emergency fund is built",
  "stability_tip": "Diversify income streams to reduce gig work volatility",
  "vacation_recommendation": "Wait 6-9 months until emergency fund is built, then budget ₹10,000 for a modest vacation"
}
```

---

## Response Format (Updated):

```json
{
  "user_id": "string",
  "summary": "string - Should answer user_query if provided",
  "top_risks": ["string"],
  "behavioral_warnings": ["string"],
  "action_steps": [
    {
      "title": "string",
      "description": "string",
      "priority": "critical | high | medium | low"
    }
  ],
  "savings_tip": "string",
  "spending_tip": "string",
  "stability_tip": "string",
  "confidence_message": "string",
  "generated_at": "ISO-8601",
  
  // Optional: Add specific answer to user query
  "query_answer": "Direct answer to user_query if provided"
}
```

---

## Testing the Integration

### Test Case 1: With User Query
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

**Expected:** Response should directly address the vacation question

### Test Case 2: Without User Query
```bash
curl -X POST http://localhost:8001/advice/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "GIG_001",
    "rules_output": {...},
    "behavior_output": {...},
    "persona_type": "gig_worker"
  }'
```

**Expected:** Response should provide general financial advice

---

## Summary of Required Changes

### Backend (Your Advice API):
1. ✅ Accept `user_query` as optional parameter
2. ✅ Update LLM prompt to prioritize answering user_query when provided
3. ✅ Provide context-aware, personalized answers
4. ✅ Add `query_answer` field to response (optional but recommended)

### Frontend (LangGraph - Already Done):
1. ✅ Pass `user_query` from state to advice API
2. ✅ Display user's question in output
3. ✅ Show all advice fields with proper formatting

---

## Priority

**🔴 CRITICAL:** The advice API MUST use the `user_query` field to provide relevant answers. Without this, users will receive generic advice that doesn't answer their questions.
