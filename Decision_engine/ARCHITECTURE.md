# Decision Engine Architecture

## Overview

The Decision Engine is a financial health assessment system that processes user financial data to produce personalized risk assessments, rule-based triggers, actionable recommendations, and time-bound action plans.

**Primary Flow:**
```
Raw JSON Input → Normalization → Rule Evaluation → Risk Aggregation → Recommendations → Action Plan → Structured Output
```

---

## Complete Processing Pipeline

### 1. Entry Point (`app/main.py`)

The FastAPI application exposes two main endpoints:

```python
POST /evaluate  # Process custom JSON payload
GET  /demo      # Process sample.json for testing
GET  /health    # Health check
```

**Flow:**
```python
@app.post("/evaluate")
def evaluate(data: Dict[str, Any]):
    result = evaluate_payload(data)  # Calls engine.engine.evaluate_payload
    return JSONResponse(content=result)
```

---

### 2. Normalization (`engine/normalization.py`)

**Purpose:** Convert flexible input formats into a strict internal model (`NormalizedInput`).

**Key Operations:**
- Handles field aliases:
  - `Category_spend` OR `category_spend`
  - `Behaviour_metrics` OR `behavior_metrics`
  - `Forecast` OR `forecast`
- Type casting (floats, strings, dicts)
- Creates nested Pydantic objects:
  - `BehaviorMetrics`
  - `Forecast`
  - `Insights`

**Computed/Derived Fields:**
```python
net_cashflow = current_month_income - current_month_expense
expense_delta_pct = (current_month_expense - avg_monthly_expense) / avg_monthly_expense
```

**Example Transformation:**
```python
# Input
{
  "Category_spend": {"Food": 4200, "Transport": 1900},
  "current_month_income": 23000,
  "current_month_expense": 20500
}

# Output
NormalizedInput(
  category_spend={"Food": 4200.0, "Transport": 1900.0},
  net_cashflow=2500.0,
  expense_delta_pct=0.0353,
  ...
)
```

---

### 3. Rule Evaluation (`engine/rules.py`)

**Purpose:** Evaluate 10 financial business rules against normalized data.

#### Rule Catalog

| Rule ID | Dimension | Condition | Example Trigger |
|---------|-----------|-----------|----------------|
| **R-DEFICIT-01** | deficit | Current expense > income | Spent ₹20,500 but earned ₹19,000 |
| **R-OVRSPEND-01** | overspend | Current expense > avg by >10% | This month ₹20,500 vs avg ₹19,800 (+3.5%) |
| **R-FCAST-DEF-01** | deficit | Forecast predicts deficit (confidence ≥70%) | Next month shows deficit with 83% confidence |
| **R-SAVE-LOW-01** | savings | Savings rate < persona minimum | Gig worker at 11% savings (needs 25%) |
| **R-VOL-INC-01** | volatility | Income volatility > threshold | 22% volatility (gig threshold: 30%) |
| **R-STAB-LOW-01** | stability | Cashflow stability < 0.8 | Stability at 0.75 |
| **R-DISC-HIGH-01** | discretionary | Discretionary ratio > 0.25 | Spending 28% on discretionary items |
| **R-HSD-01** | discretionary | High-spend days > 6 | 8 high-spend days in month |
| **R-CAT-DRIFT-01** | category_outlier | Category increased ≥30% | "Entertainment up by 40%" |
| **R-TOP-CAT-HEAVY-01** | category_outlier | One category > 25% of total | Food accounts for 35% of spending |

#### Severity Assignment

Each triggered rule assigns severity based on magnitude:

**Example - Deficit Rule:**
```python
gap_pct = gap / income
if gap_pct < 0.05:    severity = "low"
elif gap_pct < 0.15:  severity = "medium"
else:                 severity = "high"
```

#### Output Structure

```python
RuleTrigger(
    rule_id="R-SAVE-LOW-01",
    triggered=True,
    severity="high",
    params={
        "current_rate": 0.11,
        "target_rate": 0.25
    },
    reason="Savings rate below persona target",
    data_refs=["/savings_rate"]
)
```

---

### 4. Risk Aggregation (`engine/risks.py`)

**Purpose:** Group triggered rules into 7 risk dimensions and compute risk scores.

#### Risk Dimensions

1. **deficit** - Spending exceeds income (current or forecast)
2. **overspend** - Above historical average spending
3. **savings** - Below target savings rate
4. **volatility** - Income fluctuations too high
5. **stability** - Cashflow inconsistency
6. **discretionary** - High optional/non-essential spending
7. **category_outlier** - Unusual spending patterns in categories

#### Aggregation Logic

```python
# Map rules to dimensions
dim_map = {
    "R-DEFICIT-01": "deficit",
    "R-FCAST-DEF-01": "deficit",
    "R-OVRSPEND-01": "overspend",
    "R-SAVE-LOW-01": "savings",
    ...
}

# For each dimension:
# 1. Collect all triggered rules
# 2. Take maximum severity across rules
# 3. Convert severity to score:
#    - low: 33
#    - medium: 66
#    - high: 100
```

#### Risk Item Structure

```python
RiskItem(
    id="RK-SAVINGS",
    dimension="savings",
    score=100,
    severity="high",
    summary="Savings risk: high",
    reasons=["Savings rate below persona target"],
    data_refs=["/savings_rate"],
    contributors=[
        {
            "rule_id": "R-SAVE-LOW-01",
            "severity": "high",
            "weight": 1
        }
    ]
)
```

---

### 5. Recommendation Generation (`engine/recommendations.py`)

**Purpose:** Translate triggered rules and risks into actionable advice with specific amounts and steps.

#### Recommendation Catalog

| ID | Triggered By | Purpose | Example |
|----|--------------|---------|---------|
| **REC-BALANCE-01** | R-DEFICIT-01 | Close monthly gap | "Reduce discretionary by 15% (₹3,075)" |
| **REC-SAVE-BOOST-01** | R-SAVE-LOW-01 | Increase savings rate | "Set auto-transfer of ₹6,125 to reach 25%" |
| **REC-BUFFER-01** | R-VOL-INC-01 | Build income buffer | "Build 6-month buffer of ₹118,800" |
| **REC-CAP-01** | R-OVRSPEND-01 | Set spending cap | "Cap next month at ₹20,790 (105% of avg)" |
| **REC-CAT-AUDIT-01** | R-CAT-DRIFT-01 | Audit category spike | "Audit Entertainment, set cap at ₹2,530" |
| **REC-SPEND-ALERT-01** | R-DISC-HIGH-01, R-HSD-01 | Tighten daily spending | "Enable daily alerts & hard stops" |

#### Dynamic Calculation Examples

**Deficit Gap Calculation:**
```python
gap = current_expense - current_income  # ₹1,500
cut_pct = min(0.20, max(0.10, gap / current_expense))  # 10-20% range
cut_amt = current_expense * cut_pct
```

**Buffer Target Calculation:**
```python
n_months = 6 if persona == "gig_worker" else 3
buffer_target = n_months * avg_monthly_expense
```

#### Recommendation Structure

```python
Recommendation(
    id="REC-SAVE-BOOST-01",
    title="Boost savings rate",
    body="Savings rate is below target. Set auto-transfer to reach 25% upon income receipt.",
    actions=[
        "Create automated savings transfer on payday"
    ],
    amounts={
        "new_savings_rate": 0.25
    },
    linked_risks=["RK-SAVINGS-01"],
    priority=2,
    valid_for_days=30,
    data_refs=["/savings_rate"]
)
```

---

### 6. Action Plan Generation (`engine/recommendations.py`)

**Purpose:** Convert recommendations into time-bound tasks with KPIs.

```python
{
    "next_30_days": [
        {
            "action_id": "REC-BALANCE-01",
            "title": "Close this month's gap",
            "kpi": "complete_action",
            "target": 1,
            "owner": "user"
        },
        ...
    ],
    "next_90_days": [],  # Currently unused
    "kpis": []
}
```

---

### 7. Final Output Assembly (`engine/engine.py`)

**Purpose:** Package all components into the final structured response.

```python
{
    "metadata": {
        "user_id": "U12345",
        "month": "2025-10",
        "persona": "gig_worker",
        "currency": "₹",
        "generated_at": "2025-11-18T14:32:00Z",
        "engine_version": "1.0.0",
        "confidence": 0.89
    },
    "risks": [...],                    # List of RiskItem
    "rule_triggers": [...],            # Only triggered rules
    "recommendations": [...],          # List of Recommendation
    "action_plan": {...},              # Next 30/90 day tasks
    "alerts": [],                      # Reserved for future use
    "audit": {
        "input_fields": [...],
        "normalization": {...}
    }
}
```

---

## Configuration System (`engine/config.py`)

All business thresholds and weights are centralized in `DEFAULTS`:

```python
DEFAULTS = {
    "currency": "₹",
    
    # Persona-based savings minimums
    "persona_min_savings": {
        "gig_worker": 0.25,   # 25% minimum
        "salaried": 0.20,     # 20% minimum
        "default": 0.20
    },
    
    # Income volatility thresholds
    "volatility_threshold": {
        "gig_worker": 0.30,
        "salaried": 0.20,
        "default": 0.25
    },
    
    # Severity bands
    "stability_thresholds": {
        "low": 0.8,
        "high": 0.6
    },
    "overspend_bands": {
        "low": 0.10,
        "med": 0.20,
        "high": 0.35
    },
    "discretionary_ratio_bands": {
        "low": 0.25,
        "med": 0.35
    },
    "deficit_bands": {
        "low": 0.05,
        "med": 0.15
    },
    
    # Risk dimension weights (currently unused in modular engine)
    "weights": {
        "deficit": 0.30,
        "overspend": 0.20,
        "volatility": 0.15,
        "stability": 0.15,
        "savings": 0.10,
        "discretionary": 0.05,
        "category_outlier": 0.05
    },
    
    # Category classifications
    "discretionary_categories": {
        "Entertainment", "Leisure", "Eating Out", "Shopping"
    },
    
    # Essential spending protection
    "essential_min_caps": {
        "Utilities": 0.9,  # Won't recommend cutting below 90%
        "Health": 0.9
    }
}
```

### Helper Function

```python
def persona_value(mapping: Dict[str, float], persona: str) -> float:
    """Retrieve persona-specific value with fallback to default"""
    return mapping.get(persona or "", mapping.get("default"))
```

---

## Complete Example Walkthrough

### Input (`sample.json`)

```json
{
  "user_id": "U12345",
  "month": "2025-10",
  "avg_monthly_income": 24500,
  "avg_monthly_expense": 19800,
  "current_month_income": 23000,
  "current_month_expense": 20500,
  "savings_rate": 0.11,
  "income_volatility": 0.22,
  "risk_level": "moderate",
  "Category_spend": {
    "Food": 4200,
    "Transport": 1900,
    "Entertainment": 2300,
    "Utilities": 2600,
    "Health": 800
  },
  "Behaviour_metrics": {
    "avg_daily_expense": 700,
    "high_spend_days": 5,
    "cashflow_stability": 0.75,
    "discretionary_ratio": 0.28
  },
  "Forecast": {
    "predicted_income_next_month": 24000,
    "predicted_expense_next_month": 19000,
    "savings": 5000,
    "confidence": 0.83
  },
  "persona_type": "gig_worker",
  "confidence_score": 0.89,
  "insights": {
    "top_spend_category": "Food",
    "category_drift": "Entertainment up by 40%"
  }
}
```

### Processing Steps

#### 1. Normalization
```
✓ net_cashflow = 23000 - 20500 = 2500
✓ expense_delta_pct = (20500 - 19800) / 19800 = 0.0353 (3.53%)
```
 
#### 2. Rule Evaluation

| Rule | Triggered? | Severity | Reason |
|------|-----------|----------|--------|
| R-DEFICIT-01 | ❌ No | - | Income (23k) > Expense (20.5k) |
| R-OVRSPEND-01 | ❌ No | - | Only 3.53% over average (needs >10%) |
| R-FCAST-DEF-01 | ❌ No | - | Forecast shows surplus (24k > 19k) |
| R-SAVE-LOW-01 | ✅ **Yes** | **high** | 11% < 25% (gig_worker minimum) |
| R-VOL-INC-01 | ❌ No | - | 22% < 30% (gig_worker threshold) |
| R-STAB-LOW-01 | ✅ **Yes** | **medium** | 0.75 < 0.8 |
| R-DISC-HIGH-01 | ✅ **Yes** | **medium** | 28% > 25% |
| R-HSD-01 | ❌ No | - | 5 days ≤ 6 days |
| R-CAT-DRIFT-01 | ✅ **Yes** | **medium** | Entertainment +40% ≥ 30% |
| R-TOP-CAT-HEAVY-01 | ❌ No | - | Food is 20.5% < 25% |

#### 3. Risk Aggregation

```
RK-SAVINGS
  - Score: 100 (high)
  - Contributors: R-SAVE-LOW-01

RK-STABILITY
  - Score: 66 (medium)
  - Contributors: R-STAB-LOW-01

RK-DISCRETIONARY
  - Score: 66 (medium)
  - Contributors: R-DISC-HIGH-01

RK-CATEGORY_OUTLIER
  - Score: 66 (medium)
  - Contributors: R-CAT-DRIFT-01
```

#### 4. Recommendations Generated

**REC-SAVE-BOOST-01:**
```
Title: Boost savings rate
Target: Auto-transfer ₹6,125 (25% of avg income)
Priority: 2
```

**REC-CAT-AUDIT-01:**
```
Title: Audit category: Entertainment
Temporary cap: ₹2,530 (110% of current)
Priority: 3
```

**REC-SPEND-ALERT-01:**
```
Title: Tighten daily spending
Action: Enable daily alerts & hard stops
Priority: 3
```

#### 5. Action Plan

```json
{
  "next_30_days": [
    {
      "action_id": "REC-SAVE-BOOST-01",
      "title": "Boost savings rate to persona minimum",
      "kpi": "complete_action",
      "target": 1
    },
    {
      "action_id": "REC-CAT-AUDIT-01",
      "title": "Audit category: Entertainment",
      "kpi": "complete_action",
      "target": 1
    },
    {
      "action_id": "REC-SPEND-ALERT-01",
      "title": "Tighten daily spending",
      "kpi": "complete_action",
      "target": 1
    }
  ],
  "next_90_days": [],
  "kpis": []
}
```

---

## Data Models (`engine/models.py`)

### Core Input Model

```python
class NormalizedInput(BaseModel):
    # Identifiers
    user_id: str
    month: str
    
    # Financial metrics
    avg_monthly_income: float
    avg_monthly_expense: float
    current_month_income: float
    current_month_expense: float
    savings_rate: Optional[float]
    income_volatility: Optional[float]
    risk_level: Optional[Literal["low", "moderate", "high"]]
    
    # Nested data
    category_spend: Dict[str, float]
    behavior_metrics: Optional[BehaviorMetrics]
    forecast: Optional[Forecast]
    
    # Context
    persona_type: Optional[str]
    confidence_score: Optional[float]
    insights: Optional[Insights]
    
    # Derived (computed during normalization)
    net_cashflow: float
    expense_delta_pct: Optional[float]
```

### Output Models

```python
class RuleTrigger(BaseModel):
    rule_id: str
    triggered: bool
    severity: Optional[Literal["low", "medium", "high"]]
    params: Dict[str, Any]
    reason: Optional[str]
    data_refs: List[str]

class RiskItem(BaseModel):
    id: str
    dimension: Literal["deficit", "overspend", "savings", ...]
    score: int  # 0, 33, 66, or 100
    severity: Literal["low", "medium", "high", "none"]
    summary: str
    reasons: List[str]
    data_refs: List[str]
    contributors: List[Dict[str, Any]]

class Recommendation(BaseModel):
    id: str
    title: str
    body: str
    actions: List[str]
    amounts: Dict[str, Any]
    linked_risks: List[str]
    priority: int  # 1=highest
    valid_for_days: int
    data_refs: List[str]
```

---

## Key Design Principles

### 1. Deterministic Behavior
- Same input **always** produces same output
- No random elements or external API calls
- Fully testable and reproducible

### 2. Persona-Aware Logic
- Different thresholds for `gig_worker` vs `salaried` vs `default`
- Buffer recommendations vary (6 months vs 3 months)
- Configurable via `config.DEFAULTS`

### 3. Traceability
- Every risk links to contributing rules
- Every recommendation links to risks
- `data_refs` point to exact input fields used

### 4. Extensibility
- Add new rules in `rules.py` without touching other files
- Add new dimensions by updating `dim_map` in `risks.py`
- Add new recommendations by extending `build_recommendations()`

### 5. Separation of Concerns
```
Normalization  → Clean data structure
Rules          → Business logic evaluation
Risks          → Aggregation & scoring
Recommendations → Actionable guidance
```

---

## Known Limitations & Technical Debt

### 1. Duplicate Engine
- `app/engine.py` contains a standalone implementation
- Not used by the API (uses `engine.engine.evaluate_payload`)
- Should be deprecated or refactored

### 2. Unused Configuration
- `DEFAULTS["weights"]` defined but not used to compute composite score
- Only the duplicate engine uses weighted aggregation

### 3. Parsing Brittleness
- Category drift relies on regex: `r"(\w[\w\s&-]*)\s+up\s+by\s+(\d+)%"`
- Fails for variations like "increased 40%" or "down by 20%"

### 4. Action Plan Gaps
- `next_90_days` always empty
- Could include buffer-building or savings milestones

### 5. Field Naming Inconsistency
- Mixed `Behaviour_metrics` vs `behavior_metrics`
- Handled via aliases but creates confusion

### 6. Missing Features
- No logging/tracing for debugging
- No unit tests
- No overall composite risk score (0-100)
- Version hardcoded instead of from single source

---

## Potential Improvements

### High Priority
1. **Consolidate Engines** - Remove or refactor `app/engine.py`
2. **Add Composite Risk Score** - Use `DEFAULTS["weights"]` to compute 0-100 overall score
3. **Unit Tests** - Cover normalization, each rule, recommendations
4. **Fix Stability Threshold Naming** - `"low": 0.8, "high": 0.6` is confusing

### Medium Priority
5. **Enhance Category Drift Parser** - Support more patterns, handle decreases
6. **Expand Action Plan** - Populate `next_90_days` with buffer/savings goals
7. **Add Logging** - Structured logs for each pipeline stage
8. **Input Validation** - Clamp negative spends, validate date format

### Nice to Have
9. **External Config** - Load thresholds from YAML/JSON
10. **Performance Optimization** - Precompute band thresholds (minor impact)
11. **Security Hardening** - Sanitize regex inputs
12. **Documentation** - Add docstrings to all functions

---

## API Usage Examples

### Basic Evaluation

```bash
# POST custom payload
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @sample.json

# GET demo output (uses sample.json)
curl http://localhost:8000/demo

# Health check
curl http://localhost:8000/health
```

### Python Client

```python
import requests

payload = {
    "user_id": "U12345",
    "month": "2025-11",
    "avg_monthly_income": 25000,
    "current_month_income": 24000,
    # ... other fields
}

response = requests.post(
    "http://localhost:8000/evaluate",
    json=payload
)

result = response.json()
print(f"Risks: {len(result['risks'])}")
print(f"Recommendations: {len(result['recommendations'])}")
```

---

## Running the Engine

### Installation

```bash
pip install -r requirements.txt
```

### Start API Server

```bash
uvicorn app.main:app --reload
# or
python -m app.main
```

### Run Sample Script

```bash
python scripts/run_sample.py
```

---

## Summary

The Decision Engine is a **modular, rules-based financial assessment system** that:

1. ✅ Normalizes flexible input formats
2. ✅ Evaluates 10 deterministic business rules
3. ✅ Aggregates risks across 7 dimensions
4. ✅ Generates personalized, actionable recommendations
5. ✅ Produces time-bound action plans
6. ✅ Returns fully traceable, structured JSON output

**Core Value:** Transforms raw financial data into **immediate, specific, persona-aware guidance** for users to improve their financial health.
