# Weighted Risk Scoring System

## Overview

The Decision Engine uses a **sophisticated weighted risk scoring** system that calculates risk scores based on both the severity of triggered rules and their assigned weights.

## How It Works

### Formula
```
risk_score = Σ(weight × severity_multiplier)
normalized_score = (risk_score / max_possible_score) × 100
```

### Severity Multipliers
- **low**: 1.0×
- **medium**: 2.0×
- **high**: 3.0×
- **none**: 0.0×

### Example Calculation

Given these triggered rules in the "savings" dimension:
- R-SAVE-LOW-01: severity="low", weight=1.5
- R-BUFFER-WARN-01: severity="medium", weight=2.0

**Calculation:**
```
weighted_score = (1.5 × 1.0) + (2.0 × 2.0)
               = 1.5 + 4.0
               = 5.5

max_possible_score = (1.5 × 3.0) + (2.0 × 3.0)
                   = 4.5 + 6.0
                   = 10.5

normalized_score = (5.5 / 10.5) × 100
                 = 52.4 (out of 100)
```

## Rule Weights

### Default Weight
All rules default to **weight = 1.0** if not specified in the rule definition.

### Configuring Weights

#### In JSON Registry (Dynamic Rules)
```json
{
  "id": "R-DEFICIT-01",
  "bucket": "budget_stability",
  "name": "Current Month Deficit",
  "enabled": true,
  "priority": 1,
  "weight": 2.0,   ← Higher weight = more impact on risk score
  "condition": { ... }
}
```

#### Recommended Weight Guidelines

| Importance | Weight Range | Use Cases |
|------------|--------------|-----------|
| **Critical** | 2.0 - 3.0 | Immediate financial danger (deficit, no emergency fund) |
| **High** | 1.5 - 2.0 | Serious issues requiring action (low savings, high volatility) |
| **Medium** | 1.0 - 1.5 | Important but not urgent (category drift, overspend) |
| **Low** | 0.5 - 1.0 | Advisory signals (forecasts, trends) |

### Example Weight Assignments

```json
{
  "R-DEFICIT-01": 2.5,           // Critical: Current deficit
  "R-SAVE-LOW-01": 1.5,          // High: Low savings rate
  "R-OVRSPEND-01": 1.0,          // Medium: Overspending
  "R-CAT-DRIFT-01": 0.8,         // Medium-Low: Category drift
  "R-FCAST-DEF-01": 1.2,         // Medium: Forecasted issue
  "R-VOL-INC-01": 2.0,           // High: Income volatility (esp. gig workers)
  "R-DISC-HIGH-01": 1.0          // Medium: Discretionary spending
}
```

## Risk Output Structure

Each `RiskItem` now includes weighted scoring information:

```json
{
  "id": "RK-SAVINGS",
  "dimension": "savings",
  "score": 52.4,                      // Normalized 0-100 score
  "severity": "medium",               // Overall severity (max of contributors)
  "summary": "Savings risk: medium",
  "reasons": ["...", "..."],
  "data_refs": [...],
  "contributors": [
    {
      "rule_id": "R-SAVE-LOW-01",
      "severity": "low",
      "weight": 1.5
    },
    {
      "rule_id": "R-BUFFER-WARN-01",
      "severity": "medium",
      "weight": 2.0
    }
  ],
  "weighted_score": 5.5,              // Raw weighted score
  "max_possible_score": 10.5          // Maximum if all rules were "high"
}
```

## Benefits

### 1. **Nuanced Risk Assessment**
- Not all rules are equally important
- Critical issues get more weight in final score
- Better reflects actual risk severity

### 2. **Persona-Specific Tuning**
Different personas can have different weights:
```json
{
  "gig_worker": {
    "R-VOL-INC-01": 2.5,    // Very important for gig workers
    "R-SAVE-LOW-01": 2.0    // Extra important with irregular income
  },
  "salaried": {
    "R-VOL-INC-01": 1.0,    // Less critical for salaried
    "R-SAVE-LOW-01": 1.5    // Still important but less urgent
  }
}
```
*(Future enhancement - currently uses single weight per rule)*

### 3. **Comparative Analysis**
- Compare risk scores across time periods
- Identify which rules contribute most to risk
- Track improvement as issues are resolved

### 4. **Actionable Prioritization**
- Higher weighted scores = higher priority
- Recommendations can be ordered by risk impact
- Focus on high-weight, high-severity combinations

## Implementation Details

### In `models.py`
```python
class RuleTrigger(BaseModel):
    rule_id: str
    triggered: bool
    severity: Optional[Literal["low", "medium", "high"]] = None
    weight: float = 1.0  # ← Added weight field
    params: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
    data_refs: List[str] = Field(default_factory=list)
```

### In `risks.py`
```python
def _severity_to_multiplier(severity: str) -> float:
    return {"none": 0.0, "low": 1.0, "medium": 2.0, "high": 3.0}.get(severity, 1.0)

def _calculate_weighted_score(contributors: List[Dict]) -> Tuple[float, float, str]:
    weighted_score = sum(c["weight"] * _severity_to_multiplier(c["severity"]) 
                        for c in contributors)
    max_possible_score = sum(c["weight"] * 3.0 for c in contributors)
    # Normalize to 0-100
    normalized = (weighted_score / max_possible_score * 100) if max_possible_score > 0 else 0
    return weighted_score, max_possible_score, overall_severity
```

## Usage Examples

### Example 1: Analyze Risk Breakdown
```python
from engine.engine import evaluate_payload

result = evaluate_payload(financial_data, use_dynamic_rules=True)

for risk in result["risks"]:
    print(f"\n{risk['id']}: {risk['summary']}")
    print(f"  Score: {risk['score']:.1f}/100")
    print(f"  Weighted: {risk['weighted_score']:.1f}/{risk['max_possible_score']:.1f}")
    print(f"  Contributors:")
    for c in risk["contributors"]:
        impact = c["weight"] * _severity_to_multiplier(c["severity"])
        print(f"    - {c['rule_id']}: weight={c['weight']}, severity={c['severity']}, impact={impact}")
```

### Example 2: Compare Before/After
```python
# Before taking action
result_before = evaluate_payload(data_before, use_dynamic_rules=True)
savings_risk_before = next(r for r in result_before["risks"] if r["id"] == "RK-SAVINGS")

# After implementing recommendations
result_after = evaluate_payload(data_after, use_dynamic_rules=True)
savings_risk_after = next(r for r in result_after["risks"] if r["id"] == "RK-SAVINGS")

improvement = savings_risk_before["score"] - savings_risk_after["score"]
print(f"Savings risk improved by {improvement:.1f} points")
```

### Example 3: Prioritize by Weighted Impact
```python
result = evaluate_payload(data, use_dynamic_rules=True)

# Sort risks by weighted score
sorted_risks = sorted(result["risks"], 
                     key=lambda r: r["weighted_score"], 
                     reverse=True)

print("Top 3 risks by weighted score:")
for risk in sorted_risks[:3]:
    print(f"  {risk['id']}: {risk['weighted_score']:.1f} ({risk['severity']})")
```

## Best Practices

### 1. **Start with Default Weights (1.0)**
   - Test the system with equal weights first
   - Identify which rules need adjustment

### 2. **Calibrate Gradually**
   - Adjust weights based on real data
   - Compare with expert judgment
   - Iterate based on user feedback

### 3. **Document Weight Rationale**
   - Explain why each weight was chosen
   - Update as business requirements evolve

### 4. **Consider Persona Differences**
   - Plan for persona-specific weights (future)
   - Same rule may have different importance

### 5. **Monitor Score Distribution**
   - Ensure scores spread across 0-100 range
   - Avoid all scores clustering at extremes

## Future Enhancements

- [ ] **Persona-Specific Weights**: Different weights per user type
- [ ] **Dynamic Weight Adjustment**: ML-based weight optimization
- [ ] **Temporal Weighting**: Recent issues weighted higher
- [ ] **Contextual Weighting**: Adjust based on user goals
- [ ] **Weight Decay**: Older triggered rules lose weight over time
- [ ] **Composite Risk Scores**: Cross-dimension risk aggregation

## Migration Notes

### For Existing Systems
1. All existing rules get `weight=1.0` by default
2. Risk scores will change but relative ordering may stay similar
3. Update dashboards to show weighted scores
4. Recalibrate thresholds if needed

### Backward Compatibility
- Old code without weights continues to work (defaults to 1.0)
- Legacy `score` field preserved (0-100 normalized)
- New `weighted_score` and `max_possible_score` fields added

---

**Version**: 1.0  
**Last Updated**: 2025-11-24  
**Status**: ✅ Production Ready
