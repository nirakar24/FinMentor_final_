from __future__ import annotations

from datetime import datetime
from typing import Dict, Any
import os

from .normalization import normalize_input
from .rules import eval_rules
from .risks import build_risks
from .recommendations import build_recommendations, build_action_plan

# Import dynamic rule evaluator
try:
    from .rule_registry import eval_rules_dynamic
    DYNAMIC_RULES_AVAILABLE = True
except ImportError:
    DYNAMIC_RULES_AVAILABLE = False


def evaluate_payload(raw: Dict[str, Any], use_dynamic_rules: bool = None) -> Dict[str, Any]:
    data = normalize_input(raw)
    
    # Determine which rule engine to use
    if use_dynamic_rules is None:
        # Check environment variable or default to dynamic if available
        use_dynamic_rules = os.getenv("USE_DYNAMIC_RULES", "true").lower() == "true" and DYNAMIC_RULES_AVAILABLE
    
    # Evaluate rules using selected engine
    if use_dynamic_rules and DYNAMIC_RULES_AVAILABLE:
        rules = eval_rules_dynamic(data)
        engine_mode = "dynamic"
    else:
        rules = eval_rules(data)
        engine_mode = "hardcoded"
    
    risks = build_risks(data, rules)
    recs = build_recommendations(data, risks, rules)
    plan = build_action_plan(recs)

    out = {
        "metadata": {
            "user_id": data.user_id,
            "month": data.month,
            "persona": data.persona_type,
            "currency": "₹",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "engine_version": "1.0.0",
            "engine_mode": engine_mode,
            "confidence": data.confidence_score,
        },
        "risks": [r.model_dump() for r in risks],
        "rule_triggers": [r.model_dump() for r in rules if r.triggered],
        "recommendations": [r.model_dump() for r in recs],
        "action_plan": plan,
        "alerts": [],
        "audit": {
            "input_fields": [
                # Normalize field names to canonical snake_case
                "category_spend" if k in ["Category_spend", "category_spend"] else
                "behavior_metrics" if k in ["Behaviour_metrics", "behavior_metrics"] else
                "forecast" if k in ["Forecast", "forecast"] else
                k.lower().replace(" ", "_")
                for k in raw.keys()
            ],
            "normalization": {
                "used_aliases": ["category_spend", "behavior_metrics", "forecast"],
            },
            "rules_evaluated": len(rules),
            "rules_triggered": len([r for r in rules if r.triggered]),
        },
    }
    return out
