# Backend Integration Guide

## Overview
This LangGraph agent orchestrates 4 backend APIs to provide personalized financial coaching. This document explains how each API should be implemented.

---

## API Architecture

```
┌─────────────┐
│  LangGraph  │
│   Agent     │
└──────┬──────┘
       │
       ├─► 1. GET  /snapshot/{user_id}      → User financial data
       ├─► 2. POST /evaluate                → Rule engine analysis
       ├─► 3. POST /behavior/detect         → Behavior pattern detection
       └─► 4. POST /advice/generate         → LLM-powered advice (ANSWERS USER QUESTIONS)
```

---

## 1. Snapshot API ✅ WORKING

### Endpoint
```
GET http://localhost:8001/snapshot/{user_id}
```

### Response Structure (Nested Objects)
```json
{
  "user_id": "GIG_001",
  "profile": {
    "name": "Rajesh Kumar",
    "persona": "gig_worker",  // ⚠️ Used for persona_type
    "age": 28,
    "location": "Mumbai"
  },
  "income": {
    "average_monthly": 55000,  // ⚠️ Used in rule engine
    "stability_score": 42
  },
  "spending": {
    "total_monthly": 48000,    // ⚠️ Used in rule engine
    "discretionary_ratio": 0.31
  },
  "savings": {
    "current_balance": 12000,
    "emergency_fund_months": 0.22,
    "monthly_savings_rate": 0.13  // ⚠️ Used in rule engine
  },
  "debt": {
    "total_outstanding": 45000,
    "monthly_emi": 3500
  },
  "financial_health_score": 38,
  "timestamp": "2025-11-29T01:01:12.383319Z"
}
```

### ✅ Implementation Status
- [x] Nested structure with profile, income, spending, savings, debt
- [x] Returns all required fields
- [x] Handles gig_worker persona

---

## 2. Rule Engine API ✅ WORKING

### Endpoint
```
POST http://localhost:8001/evaluate
```

### Request Payload
```json
{
  "user_id": "GIG_001",
  "month": "2025-11",
  "avg_monthly_income": 55000,      // From snapshot.income.average_monthly
  "avg_monthly_expense": 48000,     // From snapshot.spending.total_monthly
  "current_month_income": 55000,    // Same as avg (can be different)
  "current_month_expense": 48000    // Same as avg (can be different)
}
```

### Response Structure
```json
{
  "metadata": {
    "user_id": "GIG_001",
    "month": "2025-11",
    "persona": null,  // Optional
    "currency": "₹"
  },
  "risks": [
    {
      "id": "RK-SAVINGS",
      "dimension": "savings",
      "score": 100.0,
      "severity": "high",
      "summary": "Savings risk: high",
      "reasons": ["Savings rate below persona target"]
    }
  ],
  "rule_triggers": [
    {
      "rule_id": "R-SAVE-LOW-01",
      "triggered": true,
      "severity": "high",
      "reason": "Savings rate below persona target"
    }
  ],
  "recommendations": [
    {
      "id": "REC-SAVE-BOOST-01",
      "title": "Boost savings rate",
      "body": "Savings rate is below target. Set an auto-transfer to reach 20%.",
      "priority": 2
    }
  ],
  "action_plan": {
    "next_30_days": [],
    "next_90_days": []
  }
}
```

### ✅ Implementation Status
- [x] Accepts correct payload structure
- [x] Returns risk analysis
- [x] Provides recommendations

---

## 3. Behavior Detection API ✅ WORKING

### Endpoint
```
POST http://localhost:8001/behavior/detect
```

### Request Payload
```json
{
  "user_id": "GIG_001",
  "avg_daily_expense": 1600.0,      // total_monthly / 30
  "high_spend_days": 0,             // From snapshot (if available)
  "cashflow_stability": 0.0,        // From snapshot (if available)
  "discretionary_ratio": 0.31       // From snapshot.spending.discretionary_ratio
}
```

### Response Structure
```json
{
  "user_id": "GIG_001",
  "behavior_flags": [
    "high_discretionary_spender",
    "unstable_cashflow"
  ],
  "behavior_score": 40,
  "risk_level": "medium",
  "generated_at": "2025-11-29T01:01:13.415757+00:00"
}
```

### ✅ Implementation Status
- [x] Accepts all required fields
- [x] Returns behavior flags
- [x] Calculates behavior score

---

## 4. Advice Generator API ⚠️ NEEDS UPDATE

### Endpoint
```
POST http://localhost:8001/advice/generate
```

### Current Request Payload (from LangGraph)
```json
{
  "user_id": "GIG_001",
  "rules_output": {
    "metadata": {...},
    "risks": [...],
    "rule_triggers": [...],
    "recommendations": [...],
    "risk_summary": {
      "triggered_rules": [],
      "risk_level": "unknown",
      "risk_score": 0,
      "recommendations": []
    },
    "normalized_data": {
      "avg_monthly_income": 55000,
      "avg_monthly_expense": 48000,
      "savings_rate": 0.13,
      "income_volatility": 0.58
    }
  },
  "behavior_output": {
    "user_id": "GIG_001",
    "behavior_flags": ["high_discretionary_spender", "unstable_cashflow"],
    "behavior_score": 40,
    "risk_level": "medium"
  },
  "persona_type": "gig_worker",
  "user_query": "Can I go on a vacation?"  // ⚠️ CRITICAL - Must be used!
}
```

### ⚠️ PROBLEM: user_query is ignored

**Current behavior**: API returns generic financial advice regardless of user_query

**Expected behavior**: API should DIRECTLY ANSWER the user's question using LLM

### 🔧 Required Implementation

Your advice API should:

1. **Extract user_query from payload**
```python
user_query = payload.get("user_query")
```

2. **Pass it to your LLM prompt**
```python
if user_query:
    system_prompt = f"""
    You are a financial advisor. The user asked: "{user_query}"
    
    ANSWER THEIR QUESTION FIRST, then provide additional context.
    
    Financial Context:
    - Income: ₹{normalized_data['avg_monthly_income']}
    - Expenses: ₹{normalized_data['avg_monthly_expense']}
    - Savings: ₹{normalized_data['savings_rate'] * 100}%
    - Risks: {risks}
    - Behavior: {behavior_flags}
    
    Provide a direct answer to their question with specific numbers and reasoning.
    """
else:
    system_prompt = "Provide general financial health assessment..."
```

3. **Ensure summary addresses the question**
```python
response = {
    "summary": f"Regarding '{user_query}': [DIRECT ANSWER]. {financial_context}",
    # ... rest of response
}
```

### Example Transformation

#### ❌ Current Response (Ignoring Question)
```json
{
  "summary": "Your financial health is at risk due to unstable cash flow and high discretionary spending."
}
```
**Problem**: Doesn't answer "Can I go on a vacation?"

#### ✅ Expected Response (Answering Question)
```json
{
  "summary": "Regarding your vacation question: I recommend AGAINST taking a vacation right now. Here's why: You have only ₹12,000 in savings (0.22 months of expenses) and ₹45,000 in debt. A vacation would further deplete your emergency fund. Instead, focus on building savings to ₹48,000 (1 month buffer) first. If you must travel, consider a low-budget trip under ₹3,000 after 2 months of saving."
}
```

---

## Testing Checklist

### ✅ APIs Currently Working
- [x] Snapshot returns nested structure
- [x] Rule engine receives correct values (55000, not 1.0)
- [x] Behavior detection gets proper metrics
- [x] All APIs return 200 OK

### ⚠️ Needs Fix
- [ ] **Advice API must use user_query field**
- [ ] **LLM prompt should prioritize answering the question**
- [ ] **Summary should start with the answer to user's question**

---

## Quick Test

Run this after updating your advice API:

```bash
# Test with specific question
curl -X POST http://localhost:8001/advice/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "TEST_001",
    "user_query": "Can I afford a ₹50,000 vacation?",
    "rules_output": {"normalized_data": {"avg_monthly_income": 55000, "avg_monthly_expense": 48000, "savings_rate": 0.13}},
    "behavior_output": {"behavior_flags": ["unstable_cashflow"], "risk_level": "high"},
    "persona_type": "gig_worker"
  }'
```

**Expected in response.summary**: Should mention "₹50,000 vacation" and give a YES/NO answer with reasoning.

---

## Priority Action

🔥 **Update Advice API to handle user_query** - This is the main user-facing feature. Everything else is working correctly!

See `ADVICE_API_SPEC.md` for detailed implementation guide.
