# Dynamic Rules System Guide

## Overview

The Decision Engine now supports **two modes** for rule evaluation:

1. **Hardcoded Mode**: Rules defined in Python code (`engine/rules.py`)
2. **Dynamic Mode**: Rules loaded from JSON configuration (`config/rules_registry.json`)

## Benefits of Dynamic Rules

- ✅ **No Code Changes**: Add, modify, or disable rules by editing JSON
- ✅ **Easy Testing**: Swap rule sets without redeployment
- ✅ **Version Control**: Track rule changes separately from code
- ✅ **Hot Reloading**: Reload rules without restarting (future feature)
- ✅ **Business User Friendly**: Non-developers can adjust thresholds and conditions

## How to Enable Dynamic Rules

### Option 1: Environment Variable
```bash
set USE_DYNAMIC_RULES=true
python -m uvicorn app.main:app --port 8001
```

### Option 2: API Parameter
```python
from engine.engine import evaluate_payload

result = evaluate_payload(raw_input, use_dynamic_rules=True)
```

### Check Current Mode
The output includes `engine_mode` in metadata:
```json
{
  "metadata": {
    "engine_mode": "dynamic",  // or "hardcoded"
    ...
  }
}
```

## Rule Definition Format

Rules are defined in `config/rules_registry.json`. Here's the structure:

### Basic Rule
```json
{
  "id": "R-SAVE-LOW-01",
  "bucket": "budget_stability",
  "name": "Low Savings Rate",
  "enabled": true,
  "priority": 2,
  "condition": {
    "type": "comparison",
    "left": "savings_rate",
    "operator": "<",
    "right": "persona_min_savings[persona]"
  },
  "severity": {
    "type": "threshold",
    "metric": "savings_rate / persona_min_savings[persona]",
    "rules": [
      {"condition": "< 0.5", "severity": "high"},
      {"condition": "< 1.0", "severity": "medium"}
    ]
  },
  "params": {
    "current_rate": "savings_rate",
    "target_rate": "persona_min_savings[persona]"
  },
  "message_template": "Savings rate below persona target",
  "data_refs": ["/savings_rate"],
  "recommendation_id": "REC-SAVE-BOOST-01"
}
```

### Condition Types

#### 1. Comparison
```json
{
  "type": "comparison",
  "left": "expense_delta_pct",
  "operator": ">",
  "right": 0.10
}
```
Operators: `>`, `>=`, `<`, `<=`, `==`, `!=`

#### 2. Logical AND
```json
{
  "type": "logical_and",
  "conditions": [
    {"type": "comparison", "left": "...", "operator": "...", "right": "..."},
    {"type": "comparison", "left": "...", "operator": "...", "right": "..."}
  ]
}
```

#### 3. Logical OR
```json
{
  "type": "logical_or",
  "conditions": [...]
}
```

#### 4. Null Check
```json
{
  "type": "is_null",
  "field": "emergency_fund"
}
```

#### 5. Field Exists
```json
{
  "type": "field_exists",
  "field": "forecast.confidence"
}
```

### Expression Syntax

Expressions can reference:

1. **Direct fields**: `savings_rate`, `current_month_income`
2. **Nested fields**: `behavior_metrics.cashflow_stability`, `forecast.confidence`
3. **Dictionary access**: `category_spend[Food]`, `persona_min_savings[persona]`
4. **Arithmetic**: `(current_month_expense - current_month_income) / current_month_income`
5. **Literal values**: `0.8`, `0.25`, `3`

### Severity Types

#### 1. Fixed Severity
```json
{
  "type": "fixed",
  "value": "high"
}
```

#### 2. Banded Severity
```json
{
  "type": "banded",
  "metric": "expense_delta_pct",
  "bands": [
    {"threshold": 0.10, "severity": "low"},
    {"threshold": 0.20, "severity": "medium"},
    {"threshold": null, "severity": "high"}
  ]
}
```
*Note: `threshold: null` means "everything above the previous threshold"*

#### 3. Threshold Severity
```json
{
  "type": "threshold",
  "metric": "income_volatility / volatility_threshold[persona]",
  "rules": [
    {"condition": "> 1.5", "severity": "high"},
    {"condition": "> 1.0", "severity": "medium"}
  ]
}
```

## Available Context Variables

The rule evaluator provides these variables:

### Direct Fields
- `current_month_income`
- `current_month_expense`
- `avg_monthly_income`
- `avg_monthly_expense`
- `savings_rate`
- `income_volatility`
- `net_cashflow`
- `expense_delta_pct`
- `category_spend` (dict: `category_spend[Food]`)
- `persona` (string: "gig_worker", "salaried", "default")

### Nested Objects
- `behavior_metrics.cashflow_stability`
- `behavior_metrics.discretionary_ratio`
- `behavior_metrics.high_spend_days`
- `behavior_metrics.avg_daily_expense`
- `forecast.predicted_income_next_month`
- `forecast.predicted_expense_next_month`
- `forecast.savings`
- `forecast.confidence`
- `insights.top_spend_category`
- `insights.category_drift`

### Config Values
- `persona_min_savings[persona]` - e.g., `{"gig_worker": 0.25, "salaried": 0.20}`
- `volatility_threshold[persona]`
- `overspend_bands` - `{"low": 0.10, "medium": 0.20, "high": 0.30}`
- `deficit_bands`
- `rent_threshold` - `0.35`
- `emergency_fund_months` - `3`
- `category_thresholds` - `{"food": 0.30, "transport": 0.20, ...}`
- `forecast_surplus_threshold` - `0.10`
- `forecast_confidence_min` - `0.70`

## Adding a New Rule

1. Open `config/rules_registry.json`
2. Add your rule to the `rules` array:

```json
{
  "id": "R-MY-NEW-RULE-01",
  "bucket": "budget_stability",
  "name": "My New Rule",
  "enabled": true,
  "priority": 3,
  "condition": {
    "type": "comparison",
    "left": "my_metric",
    "operator": ">",
    "right": 100
  },
  "severity": {
    "type": "fixed",
    "value": "medium"
  },
  "params": {
    "metric_value": "my_metric"
  },
  "message_template": "My metric exceeded threshold",
  "data_refs": ["/my_metric"],
  "recommendation_id": "REC-MY-ACTION-01"
}
```

3. Save the file
4. If the server is running with `--reload`, changes are picked up automatically
5. Otherwise, restart the server

## Testing Rules

### Test a Single Rule
Create a test script:
```python
from engine.rule_registry import get_rule_registry, RuleEvaluator
from engine.normalization import normalize_input
import json

# Load test data
with open("sample.json") as f:
    raw_data = json.load(f)

# Normalize
data = normalize_input(raw_data)

# Load registry
registry = get_rule_registry()
evaluator = RuleEvaluator(registry)

# Evaluate specific rule
rule = registry.get_rule_by_id("R-SAVE-LOW-01")
trigger = evaluator._evaluate_rule(rule, data)

print(f"Triggered: {trigger.triggered}")
print(f"Severity: {trigger.severity}")
print(f"Params: {trigger.params}")
```

### Compare Modes
```python
from engine.engine import evaluate_payload
import json

with open("sample.json") as f:
    raw_data = json.load(f)

# Test hardcoded mode
result_hardcoded = evaluate_payload(raw_data, use_dynamic_rules=False)
print(f"Hardcoded: {len(result_hardcoded['rule_triggers'])} rules triggered")

# Test dynamic mode
result_dynamic = evaluate_payload(raw_data, use_dynamic_rules=True)
print(f"Dynamic: {len(result_dynamic['rule_triggers'])} rules triggered")
```

## Debugging Rules

### Enable Verbose Logging
The evaluator logs errors when rules fail:
```
Error evaluating rule R-MY-RULE-01: division by zero
```

### Common Issues

1. **"argument of type 'float' is not iterable"**
   - Fixed: The evaluator now handles numeric literals correctly
   
2. **"None value in condition"**
   - Check that all referenced fields exist in the input data
   - Use `field_exists` condition type to verify fields before using them

3. **"Invalid operator"**
   - Supported operators: `>`, `>=`, `<`, `<=`, `==`, `!=`

4. **"Expression evaluation failed"**
   - Arithmetic expressions must use valid Python syntax
   - Use parentheses for complex expressions

## Rule Registry API

### Load Registry
```python
from engine.rule_registry import get_rule_registry

registry = get_rule_registry()
# or with custom path
registry = get_rule_registry("config/rules_registry_v2.json")
```

### Get Rules
```python
# All rules
all_rules = registry.rules

# Enabled rules only
enabled = registry.get_enabled_rules()

# Specific rule
rule = registry.get_rule_by_id("R-SAVE-LOW-01")
```

### Evaluate Rules
```python
from engine.rule_registry import RuleEvaluator
from engine.normalization import normalize_input

evaluator = RuleEvaluator(registry)
data = normalize_input(raw_input)
triggers = evaluator.evaluate_all(data)

for trigger in triggers:
    if trigger.triggered:
        print(f"{trigger.rule_id}: {trigger.reason}")
```

## Rule Evaluator Capabilities

The enhanced `RuleEvaluator` provides production-ready features:

### ✅ Core Features
- **Context Preparation & Validation**: Builds complete evaluation context with safe defaults
- **Deterministic Evaluation**: Same input always produces same output (sorted by priority)
- **Comprehensive Error Handling**: All errors caught, logged, and handled gracefully
- **Strong Debug Logging**: Detailed logs for troubleshooting (enable with `debug=True`)
- **Safe Expression Resolution**: Handles numeric literals, nested fields, dict access, arithmetic
- **Severity Computation**: Supports fixed, banded, and threshold severity types
- **Parameter Extraction**: Safely extracts computed values for recommendations
- **Integration Ready**: Works seamlessly with risk buckets and recommendations
- **Evaluation Statistics**: Tracks rules evaluated, triggered, failed, and execution time

### Usage
```python
from engine.rule_registry import get_rule_registry, RuleEvaluator

registry = get_rule_registry()
evaluator = RuleEvaluator(registry, debug=True)  # Enable debug logs
triggers = evaluator.evaluate_all(normalized_data)

# Get stats
stats = evaluator.get_evaluation_stats()
print(f"Evaluated: {stats['total_rules']}, Triggered: {stats['rules_triggered']}")
```

## Current Rule Coverage

As of this version, **30 rules** are defined in the dynamic registry (full migration complete):

### Budget Stability (10 rules)
- R-DEFICIT-01: Current Month Deficit
- R-SAVE-LOW-01: Low Savings Rate
- R-OVRSPEND-01: Overspending vs Average
- R-NO-EMERGENCY-FUND-01: No Emergency Fund
- R-RENT-HEAVY-01: Rent > 35% of Income
- R-WEEKLY-SPIKE-01: Weekly Spending Spike
- R-CONSEC-DEF-01: Consecutive Deficits
- R-SAVE-DEPLETE-01: Savings Depletion
- R-ESSENTIAL-HEAVY-01: Essential Expenses Heavy
- R-BUFFER-WARN-01: Low Buffer Warning

### Volatility & Risk (8 rules)
- R-VOL-INC-01: High Income Volatility
- R-STAB-LOW-01: Low Cashflow Stability
- R-DISC-HIGH-01: High Discretionary Spending
- R-HSD-01: High Spend Days
- R-INCOME-DROP-01: Sudden Income Drop
- R-EXPENSE-VOL-01: High Expense Volatility
- R-ERRATIC-CF-01: Erratic Cashflow Pattern
- R-RISK-MISMATCH-01: Risk Level Mismatch

### Category-Based (8 rules)
- R-CAT-DRIFT-01: Category Drift Detected
- R-TOP-CAT-HEAVY-01: Top Category Heavy Spending
- R-FOOD-HIGH-01: Food Spending Too High
- R-TRANSPORT-HIGH-01: Transport Spending Too High
- R-ENTERTAINMENT-HIGH-01: Entertainment Spending Too High
- R-UTILITIES-SPIKE-01: Utilities Spending Spike
- R-CASH-WITHDRAWAL-HIGH-01: High Cash Withdrawals
- R-LOAN-EMI-HEAVY-01: High Loan EMI Burden

### Forecast-Driven (4 rules)
- R-FCAST-DEF-01: Forecasted Deficit
- R-FCAST-SURPLUS-01: Forecasted Surplus (Savings Opportunity)
- R-FCAST-CONFIDENCE-LOW-01: Low Forecast Confidence
- R-SPEND-TRAJECTORY-01: Increasing Spend Trajectory

**Status**: ✅ Full parity with hardcoded system achieved

## Future Enhancements

- [ ] Hot-reload endpoint: `POST /admin/rules/reload`
- [ ] Rule validation tool: `python scripts/validate_rules.py`
- [ ] Rule testing framework: `python scripts/test_rules.py`
- [ ] YAML support: `config/rules_registry.yaml`
- [ ] Rule versioning and rollback
- [ ] A/B testing framework for rules
- [ ] Visual rule editor UI
- [ ] Rule performance metrics

## Migration Guide

To migrate from hardcoded to dynamic rules:

1. **Identify the rule** in `engine/rules.py`
2. **Extract components**:
   - Condition logic → `condition` object
   - Severity calculation → `severity` object
   - Parameters → `params` object
3. **Create JSON definition** in `rules_registry.json`
4. **Test both modes** to ensure parity
5. **Disable hardcoded version** once validated

Example:
```python
# Before (hardcoded in rules.py)
if data.savings_rate < persona_min_savings.get(data.persona_type, 0.15):
    severity = "high" if data.savings_rate < 0.075 else "medium"
    triggers.append(RuleTrigger(
        rule_id="R-SAVE-LOW-01",
        triggered=True,
        severity=severity,
        params={
            "current_rate": data.savings_rate,
            "target_rate": persona_min_savings.get(data.persona_type, 0.15)
        },
        reason="Savings rate below persona target"
    ))
```

```json
// After (dynamic in rules_registry.json)
{
  "id": "R-SAVE-LOW-01",
  "condition": {
    "type": "comparison",
    "left": "savings_rate",
    "operator": "<",
    "right": "persona_min_savings[persona]"
  },
  "severity": {
    "type": "threshold",
    "metric": "savings_rate / persona_min_savings[persona]",
    "rules": [
      {"condition": "< 0.5", "severity": "high"},
      {"condition": "< 1.0", "severity": "medium"}
    ]
  },
  "params": {
    "current_rate": "savings_rate",
    "target_rate": "persona_min_savings[persona]"
  },
  "message_template": "Savings rate below persona target"
}
```

## Performance Considerations

- Rules are evaluated sequentially (no parallelization yet)
- Complex arithmetic expressions use Python's `eval()` (safe, but slower)
- Registry is loaded once at startup (singleton pattern)
- For high-throughput scenarios, consider caching normalized context

## Security Notes

- The `eval()` function is restricted: `eval(expr, {"__builtins__": {}}, context)`
- Only context variables are accessible (no imports, no file I/O)
- Still, validate JSON input carefully before deployment
- Consider adding input sanitization for production use

## Support

For questions or issues with dynamic rules:
1. Check this guide first
2. Review `engine/rule_registry.py` for implementation details
3. Test with `scripts/run_sample.py`
4. Check server logs for evaluation errors

---

**Last Updated**: 2025-11-24  
**Version**: 1.0.0  
**Status**: ✅ Fully Functional
