"""
Rule Registry Loader and Dynamic Rule Evaluator

Loads rules from JSON configuration and evaluates them against financial data.
Provides robust error handling, validation, and deterministic rule evaluation.
"""
from __future__ import annotations

import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .models import NormalizedInput, RuleTrigger
from .config import DEFAULTS, persona_value

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class RuleDefinition:
    """Structured representation of a rule from the registry."""
    id: str
    bucket: str
    name: str
    enabled: bool
    priority: int
    weight: float  # Weight for risk scoring
    condition: Dict[str, Any]
    severity: Dict[str, Any]
    params: Dict[str, str]
    message_template: str
    data_refs: List[str]
    recommendation_id: str


class RuleRegistry:
    """Manages loading and accessing rule definitions."""
    
    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            # Default to config/rules_registry.json relative to this file
            base_path = Path(__file__).parent.parent
            registry_path = str(base_path / "config" / "rules_registry.json")
        
        self.registry_path = registry_path
        self.rules: List[RuleDefinition] = []
        self.rule_groups: Dict[str, Dict] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load rules from JSON file."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.rule_groups = data.get("rule_groups", {})
        
        for rule_dict in data.get("rules", []):
            rule = RuleDefinition(
                id=rule_dict["id"],
                bucket=rule_dict["bucket"],
                name=rule_dict["name"],
                enabled=rule_dict.get("enabled", True),
                priority=rule_dict.get("priority", 5),
                weight=rule_dict.get("weight", 1.0),  # Default weight is 1.0
                condition=rule_dict["condition"],
                severity=rule_dict["severity"],
                params=rule_dict.get("params", {}),
                message_template=rule_dict["message_template"],
                data_refs=rule_dict.get("data_refs", []),
                recommendation_id=rule_dict.get("recommendation_id", "")
            )
            self.rules.append(rule)
    
    def get_enabled_rules(self) -> List[RuleDefinition]:
        """Get all enabled rules sorted by priority."""
        return sorted([r for r in self.rules if r.enabled], key=lambda x: x.priority)
    
    def get_rule_by_id(self, rule_id: str) -> Optional[RuleDefinition]:
        """Get a specific rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def get_rules_by_bucket(self, bucket: str) -> List[RuleDefinition]:
        """Get all rules in a specific bucket."""
        return [r for r in self.rules if r.bucket == bucket and r.enabled]


class RuleEvaluator:
    """
    Evaluates dynamic rules against financial data with robust error handling.
    
    Features:
    - Context preparation and validation
    - Safe condition evaluation
    - Deterministic severity computation
    - Comprehensive parameter extraction
    - Strong error handling and logging
    - Integration with recommendation buckets
    """
    
    def __init__(self, registry: RuleRegistry, debug: bool = False):
        self.registry = registry
        self.debug = debug
        self.evaluation_stats = {
            "total_rules": 0,
            "rules_triggered": 0,
            "rules_failed": 0,
            "evaluation_time_ms": 0
        }
    
    def evaluate_all(self, data: NormalizedInput) -> List[RuleTrigger]:
        """
        Evaluate all enabled rules against the data.
        
        Returns:
            List of RuleTrigger objects in deterministic order (sorted by rule priority)
        
        Guarantees:
        - Deterministic output (same input = same output)
        - All errors caught and logged
        - Failed rules return non-triggered triggers
        - Execution continues even if individual rules fail
        """
        start_time = datetime.now()
        rules = self.registry.get_enabled_rules()  # Already sorted by priority
        triggers: List[RuleTrigger] = []
        
        logger.info(f"Starting rule evaluation: {len(rules)} rules to evaluate")
        self.evaluation_stats["total_rules"] = len(rules)
        
        # Track triggered rule IDs to prevent duplicates (RULE-01)
        triggered_ids = set()
        
        for rule_def in rules:
            try:
                trigger = self._evaluate_rule(rule_def, data)
                
                # Skip duplicate triggers
                if trigger.triggered and trigger.rule_id in triggered_ids:
                    logger.debug(f"⊗ Skipping duplicate trigger for {trigger.rule_id}")
                    continue
                
                triggers.append(trigger)
                
                if trigger.triggered:
                    triggered_ids.add(trigger.rule_id)
                    self.evaluation_stats["rules_triggered"] += 1
                    logger.info(f"✓ Rule {rule_def.id} triggered: {trigger.reason} (severity: {trigger.severity})")
                elif self.debug:
                    logger.debug(f"✗ Rule {rule_def.id} not triggered")
                    
            except Exception as e:
                self.evaluation_stats["rules_failed"] += 1
                logger.error(f"✗ Error evaluating rule {rule_def.id}: {e}", exc_info=self.debug)
                # Return safe non-triggered trigger
                triggers.append(RuleTrigger(
                    rule_id=rule_def.id, 
                    triggered=False,
                    severity="low",
                    params={"error": str(e)},
                    reason=f"Rule evaluation failed: {str(e)[:100]}"
                ))
        
        # Calculate execution time
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        self.evaluation_stats["evaluation_time_ms"] = round(elapsed, 2)
        
        logger.info(f"Rule evaluation complete: {self.evaluation_stats['rules_triggered']}/{self.evaluation_stats['total_rules']} triggered, "
                   f"{self.evaluation_stats['rules_failed']} failed, {self.evaluation_stats['evaluation_time_ms']}ms")
        
        return triggers
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Return evaluation statistics."""
        return self.evaluation_stats.copy()
    
    def _evaluate_rule(self, rule_def: RuleDefinition, data: NormalizedInput) -> RuleTrigger:
        """
        Evaluate a single rule with full error handling.
        
        Steps:
        1. Build and validate context
        2. Evaluate condition
        3. Compute severity (if triggered)
        4. Extract params (if triggered)
        5. Format message (if triggered)
        6. Return RuleTrigger
        
        Args:
            rule_def: Rule definition from registry
            data: Normalized input data
            
        Returns:
            RuleTrigger with triggered=True/False and all metadata
            
        Raises:
            Exception: Only if critical failure (re-raised for logging)
        """
        try:
            # Step 1: Build evaluation context with validation
            context = self._build_context(data)
            if not self._validate_context(context, rule_def):
                logger.warning(f"Context validation failed for rule {rule_def.id}")
                return RuleTrigger(rule_id=rule_def.id, triggered=False)
            
            # Step 2: Evaluate condition
            triggered, extracted = self._evaluate_condition(rule_def.condition, context)
            
            if not triggered:
                return RuleTrigger(rule_id=rule_def.id, triggered=False)
            
            # Step 3: Calculate severity (deterministic)
            severity = self._calculate_severity(rule_def.severity, context, extracted)
            if not severity:
                severity = "medium"  # Default fallback
                logger.warning(f"Severity calculation failed for {rule_def.id}, using default: medium")
            
            # Step 4: Evaluate params
            params = self._evaluate_params(rule_def.params, context, extracted)
            
            # Step 5: Format message
            message = self._format_message(rule_def.message_template, params, extracted)
            
            # Step 6: Return complete trigger with weight
            return RuleTrigger(
                rule_id=rule_def.id,
                triggered=True,
                severity=severity,
                weight=rule_def.weight,  # Include rule weight
                params=params,
                reason=message,
                data_refs=rule_def.data_refs
            )
            
        except Exception as e:
            logger.error(f"Critical error in rule {rule_def.id}: {e}", exc_info=True)
            raise  # Re-raise for outer handler
    
    def _validate_context(self, context: Dict[str, Any], rule_def: RuleDefinition) -> bool:
        """
        Validate that context has necessary fields for rule evaluation.
        
        Returns:
            True if context is valid, False otherwise
        """
        # Basic validation: ensure context is a dict and not empty
        if not isinstance(context, dict) or not context:
            logger.error(f"Invalid context for rule {rule_def.id}: context is not a valid dictionary")
            return False
        
        # Check for required base fields
        required_fields = ["persona", "current_month_income", "current_month_expense"]
        for field in required_fields:
            if field not in context:
                logger.error(f"Missing required field '{field}' in context for rule {rule_def.id}")
                return False
        
        return True
    
    def _build_context(self, data: NormalizedInput) -> Dict[str, Any]:
        """
        Build evaluation context from data and config with full validation.
        
        Prepares all necessary variables for rule evaluation:
        - Direct financial fields
        - Derived metrics
        - Nested objects (behavior_metrics, forecast, insights)
        - Config thresholds and bands
        
        Returns:
            Complete context dictionary with safe default values
        """
        import statistics
        
        # Calculate derived metrics for weekly expenses
        max_weekly_expense = 0.0
        avg_weekly_expense = 0.0
        cashflow_coefficient_variation = 0.0
        if data.weekly_expenses and len(data.weekly_expenses) >= 2:
            max_weekly_expense = max(data.weekly_expenses)
            avg_weekly_expense = sum(data.weekly_expenses) / len(data.weekly_expenses)
            if len(data.weekly_expenses) >= 3 and avg_weekly_expense > 0:
                stdev_weekly = statistics.stdev(data.weekly_expenses)
                cashflow_coefficient_variation = stdev_weekly / avg_weekly_expense
        
        # Calculate max large transaction
        max_large_transaction = max(data.large_transactions) if data.large_transactions else 0.0
        
        context = {
            # Direct fields
            "current_month_income": data.current_month_income,
            "current_month_expense": data.current_month_expense,
            "avg_monthly_income": data.avg_monthly_income,
            "avg_monthly_expense": data.avg_monthly_expense,
            "savings_rate": data.savings_rate or 0.0,
            "income_volatility": data.income_volatility or 0.0,
            "net_cashflow": data.net_cashflow,
            "expense_delta_pct": data.expense_delta_pct or 0.0,
            "category_spend": data.category_spend,
            "persona": data.persona_type or "default",
            
            # Additional fields for new rules
            "emergency_fund_balance": data.emergency_fund_balance if data.emergency_fund_balance is not None else 0.0,
            "rent_or_housing": data.rent_or_housing if data.rent_or_housing is not None else 0.0,
            "consecutive_deficit_count": data.consecutive_deficit_count if data.consecutive_deficit_count is not None else 0,
            "previous_savings_balance": data.previous_savings_balance if data.previous_savings_balance is not None else 0.0,
            "current_savings_balance": data.current_savings_balance if data.current_savings_balance is not None else 0.0,
            "previous_month_income": data.previous_month_income if data.previous_month_income is not None else 0.0,
            "zero_income_days": data.zero_income_days if data.zero_income_days is not None else 0,
            "cash_withdrawals": data.cash_withdrawals if data.cash_withdrawals is not None else 0.0,
            "loan_emi_total": data.loan_emi_total if data.loan_emi_total is not None else 0.0,
            
            # Derived metrics
            "max_weekly_expense": max_weekly_expense,
            "avg_weekly_expense": avg_weekly_expense,
            "cashflow_coefficient_variation": cashflow_coefficient_variation,
            "max_large_transaction": max_large_transaction,
            
            # Nested objects
            "behavior_metrics": {},
            "forecast": {},
            "insights": {},
            
            # Config values
            "persona_min_savings": DEFAULTS["persona_min_savings"],
            "volatility_threshold": DEFAULTS["volatility_threshold"],
            "overspend_bands": DEFAULTS["overspend_bands"],
            "deficit_bands": DEFAULTS["deficit_bands"],
            "rent_threshold": DEFAULTS.get("rent_threshold", 0.35),
            "emergency_fund_months": DEFAULTS.get("emergency_fund_months", {}),
            "category_thresholds": DEFAULTS.get("category_thresholds", {}),
            "forecast_surplus_threshold": DEFAULTS.get("forecast_surplus_threshold", 0.1),
            "forecast_confidence_min": DEFAULTS.get("forecast_confidence_min", 0.7),
            "buffer_months_warning": DEFAULTS.get("buffer_months_warning", {}),
        }
        
        # Add nested objects if present
        if data.behavior_metrics:
            context["behavior_metrics"] = {
                "cashflow_stability": data.behavior_metrics.cashflow_stability if data.behavior_metrics.cashflow_stability is not None else 0.0,
                "discretionary_ratio": data.behavior_metrics.discretionary_ratio if data.behavior_metrics.discretionary_ratio is not None else 0.0,
                "high_spend_days": data.behavior_metrics.high_spend_days if data.behavior_metrics.high_spend_days is not None else 0,
                "avg_daily_expense": data.behavior_metrics.avg_daily_expense if data.behavior_metrics.avg_daily_expense is not None else 0.0,
            }
        
        if data.forecast:
            context["forecast"] = {
                "predicted_income_next_month": data.forecast.predicted_income_next_month if data.forecast.predicted_income_next_month is not None else 0.0,
                "predicted_expense_next_month": data.forecast.predicted_expense_next_month if data.forecast.predicted_expense_next_month is not None else 0.0,
                "savings": data.forecast.savings if data.forecast.savings is not None else 0.0,
                "confidence": data.forecast.confidence if data.forecast.confidence is not None else 1.0,
            }
        
        if data.insights:
            context["insights"] = {
                "top_spend_category": data.insights.top_spend_category if data.insights.top_spend_category else "",
                "category_drift": data.insights.category_drift if data.insights.category_drift else "",
            }
        
        return context
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate a condition against context with safe error handling.
        
        Supported condition types:
        - comparison: left operator right (>, >=, <, <=, ==, !=)
        - logical_and: all sub-conditions must be true
        - logical_or: at least one sub-condition must be true
        - is_null: field value is None
        - field_exists: field value is not None
        - regex_match: text matches pattern
        
        Args:
            condition: Condition definition dict
            context: Evaluation context
            
        Returns:
            Tuple of (triggered: bool, extracted_values: dict)
        """
        cond_type = condition.get("type")
        extracted = {}
        
        if not cond_type:
            logger.warning("Condition missing 'type' field")
            return False, {}
        
        if cond_type == "comparison":
            left = self._resolve_expression(condition["left"], context)
            right = self._resolve_expression(condition["right"], context)
            op = condition["operator"]
            
            if left is None or right is None:
                return False, {}
            
            result = self._compare(left, op, right)
            return result, {}
        
        elif cond_type == "logical_and":
            for sub_cond in condition["conditions"]:
                result, sub_extracted = self._evaluate_condition(sub_cond, context)
                extracted.update(sub_extracted)
                if not result:
                    return False, {}
            return True, extracted
        
        elif cond_type == "logical_or":
            for sub_cond in condition["conditions"]:
                result, sub_extracted = self._evaluate_condition(sub_cond, context)
                if result:
                    extracted.update(sub_extracted)
                    return True, extracted
            return False, {}
        
        elif cond_type == "is_null":
            field = condition["field"]
            value = self._resolve_expression(field, context)
            return value is None, {}
        
        elif cond_type == "field_exists":
            field = condition["field"]
            value = self._resolve_expression(field, context)
            return value is not None, {}
        
        elif cond_type == "regex_match":
            field = condition["field"]
            pattern = condition["pattern"]
            text = self._resolve_expression(field, context)
            
            if not text:
                return False, {}
            
            match = re.search(pattern, str(text), re.IGNORECASE)
            if not match:
                return False, {}
            
            # Extract named groups
            extract_names = condition.get("extract", [])
            for idx, name in enumerate(extract_names, start=1):
                try:
                    extracted[name] = match.group(idx).strip()
                except (IndexError, AttributeError):
                    pass
            
            # Check threshold if specified
            if "threshold" in condition:
                thr = condition["threshold"]
                field_val = extracted.get(thr["field"])
                if field_val is None:
                    return False, extracted
                try:
                    field_val = float(field_val)
                except (ValueError, TypeError):
                    return False, extracted
                
                op = thr["operator"]
                thr_val = thr["value"]
                if not self._compare(field_val, op, thr_val):
                    return False, extracted
            
            return True, extracted
        
        return False, {}
    
    def _calculate_severity(self, severity_def: Dict[str, Any], context: Dict[str, Any], extracted: Dict[str, Any]) -> Optional[str]:
        """
        Calculate severity based on definition with deterministic logic.
        
        Severity types:
        - fixed: Returns a constant severity value
        - banded: Calculates metric and selects band (deterministic thresholds)
        - threshold: Evaluates metric against conditions
        
        Args:
            severity_def: Severity definition from rule
            context: Evaluation context
            extracted: Extracted values from condition
            
        Returns:
            Severity string: "low", "medium", or "high"
            Default: "low" if calculation fails
        """
        sev_type = severity_def.get("type")
        
        if sev_type == "fixed":
            severity = severity_def.get("value", "medium")
            if self.debug:
                logger.debug(f"Fixed severity: {severity}")
            return severity
        
        elif sev_type == "banded":
            try:
                metric_expr = severity_def["metric"]
                metric_value = self._resolve_expression(metric_expr, context, extracted)
                
                if metric_value is None:
                    logger.warning(f"Banded severity: metric '{metric_expr}' resolved to None, defaulting to 'low'")
                    return "low"
                
                bands = severity_def["bands"]
                # Bands should be ordered from lowest to highest threshold
                for band in bands:
                    threshold = band["threshold"]
                    if threshold is None or metric_value >= threshold:
                        severity = band["severity"]
                        if self.debug:
                            logger.debug(f"Banded severity: metric_value={metric_value}, threshold={threshold}, severity={severity}")
                        return severity
                
                # Fallback to last band
                return bands[-1]["severity"] if bands else "low"
                
            except Exception as e:
                logger.error(f"Error in banded severity calculation: {e}")
                return "low"
        
        elif sev_type == "threshold":
            try:
                metric_expr = severity_def["metric"]
                metric_value = self._resolve_expression(metric_expr, context, extracted)
                
                if metric_value is None:
                    logger.warning(f"Threshold severity: metric '{metric_expr}' resolved to None, defaulting to 'low'")
                    return "low"
                
                rules = severity_def["rules"]
                # Evaluate rules in order (first match wins)
                for rule in rules:
                    cond_str = rule["condition"]
                    if self._eval_threshold_condition(metric_value, cond_str):
                        severity = rule["severity"]
                        if self.debug:
                            logger.debug(f"Threshold severity: metric_value={metric_value}, condition={cond_str}, severity={severity}")
                        return severity
                
                # No rules matched
                return "low"
                
            except Exception as e:
                logger.error(f"Error in threshold severity calculation: {e}")
                return "low"
        
        logger.warning(f"Unknown severity type: {sev_type}, defaulting to 'medium'")
        return "medium"
    
    def _evaluate_params(self, params: Dict[str, str], context: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate parameter expressions safely.
        
        Extracts computed values for use in recommendations and messaging.
        Skips parameters that fail to resolve (logs warning in debug mode).
        
        Args:
            params: Dict of param_name -> expression
            context: Evaluation context
            extracted: Extracted values from condition
            
        Returns:
            Dict of param_name -> resolved_value
        """
        result = {}
        for key, expr in params.items():
            try:
                value = self._resolve_expression(expr, context, extracted)
                if value is not None:
                    result[key] = value
                elif self.debug:
                    logger.debug(f"Param '{key}' resolved to None, skipping")
            except Exception as e:
                logger.warning(f"Error evaluating param '{key}': {e}")
                # Continue with other params
        return result
    
    def _format_message(self, template: str, params: Dict[str, Any], extracted: Dict[str, Any]) -> str:
        """
        Format message template with parameters (safe substitution).
        
        Supports:
        - Simple placeholders: {key}
        - Percentage placeholders: {key_pct} (for numeric values)
        - Missing placeholders are left unchanged
        
        Args:
            template: Message template string
            params: Computed parameters
            extracted: Extracted values from condition
            
        Returns:
            Formatted message string
        """
        message = template
        all_values = {**params, **extracted}
        
        for key, value in all_values.items():
            # Simple placeholder replacement
            placeholder = f"{{{key}}}"
            if placeholder in message:
                try:
                    message = message.replace(placeholder, str(value))
                except Exception as e:
                    logger.warning(f"Error formatting placeholder {{{key}}}: {e}")
            
            # Handle percentage placeholders
            pct_placeholder = f"{{{key}_pct}}"
            if pct_placeholder in message and isinstance(value, (int, float)):
                try:
                    message = message.replace(pct_placeholder, f"{int(value * 100)}")
                except Exception as e:
                    logger.warning(f"Error formatting percentage placeholder {{{key}_pct}}: {e}")
        
        return message
    
    def _resolve_expression(self, expr: str, context: Dict[str, Any], extracted: Optional[Dict[str, Any]] = None) -> Any:
        """
        Resolve an expression safely with full error handling.
        
        Supports:
        - Literal values: 0.8, 100, "text"
        - Simple fields: savings_rate
        - Nested fields: behavior_metrics.cashflow_stability
        - Dict access: category_spend[Food], persona_min_savings[persona]
        - Arithmetic: (current_month_expense - current_month_income) / current_month_income
        
        Args:
            expr: Expression string or literal value
            context: Evaluation context dict
            extracted: Extracted values from condition
            
        Returns:
            Resolved value or None if resolution fails
        """
        if extracted is None:
            extracted = {}
        
        # If expr is already a number, return it directly (handles JSON numeric literals)
        if isinstance(expr, (int, float)):
            return expr
        
        # If expr is already a bool, return it
        if isinstance(expr, bool):
            return expr
        
        # Convert to string if needed
        expr = str(expr).strip()
        
        # Empty expression
        if not expr:
            return None
        
        # Check extracted values first
        if expr in extracted:
            try:
                return float(extracted[expr])
            except (ValueError, TypeError):
                return extracted[expr]
        
        # Handle simple field access
        if expr in context:
            return context[expr]
        
        # Handle nested access like 'behavior_metrics.cashflow_stability'
        if '.' in expr and '[' not in expr:
            try:
                parts = expr.split('.')
                value = context
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return None
                    if value is None:
                        return None
                return value
            except Exception as e:
                logger.warning(f"Error resolving nested expression '{expr}': {e}")
                return None
        
        # Check if this is arithmetic expression (contains operators) before treating as simple dict access
        # This prevents "category_spend[Food] / current_month_income" from being treated as simple bracket access
        has_arithmetic = any(op in expr for op in ['+', '-', '*', '/', '(', ')'])
        
        # Handle dictionary access like 'category_spend[Food]' or 'persona_min_savings[persona]'
        # Only if it's NOT an arithmetic expression
        if '[' in expr and ']' in expr and not has_arithmetic:
            try:
                base = expr[:expr.index('[')]
                key = expr[expr.index('[') + 1:expr.index(']')]
                
                # Resolve base
                base_value = context.get(base)
                if base_value is None:
                    return None
                
                # Resolve key (might be a variable reference)
                if key in context:
                    key = context[key]
                
                if isinstance(base_value, dict):
                    return base_value.get(key)
                
                return None
            except Exception as e:
                logger.warning(f"Error resolving dict access expression '{expr}': {e}")
                return None
        
        # Handle arithmetic expressions (safe eval with restricted builtins)
        try:
            # Pre-process bracket notation in arithmetic expressions
            # e.g., "category_spend[Food] / current_month_income" -> resolve category_spend[Food] first
            processed_expr = expr
            import re
            bracket_pattern = r'(\w+)\[([^\]]+)\]'
            
            def replace_bracket(match):
                base = match.group(1)
                key = match.group(2)
                # Resolve the bracket notation
                base_value = context.get(base)
                if base_value is None:
                    return "0"  # Fallback to 0 if base not found
                # Resolve key (might be a variable)
                if key in context:
                    key = str(context[key])
                if isinstance(base_value, dict):
                    val = base_value.get(key, 0)
                    return str(val)
                return "0"
            
            processed_expr = re.sub(bracket_pattern, replace_bracket, expr)
            
            # Safe eval with context - no builtins accessible
            result = eval(processed_expr, {"__builtins__": {}}, context)
            
            # Validate numeric ranges (NUM-01): ratios should be 0-10 (0% to 1000%)
            if isinstance(result, (int, float)):
                if result < 0 or result > 10:
                    logger.warning(f"Expression '{expr}' = {result} is outside expected ratio range [0, 10]")
            
            return result
        except Exception as e:
            if self.debug:
                logger.debug(f"Expression '{expr}' failed to evaluate: {e}")
            return None
    
    def _compare(self, left: Any, op: str, right: Any) -> bool:
        """
        Perform safe comparison with type handling.
        
        Supported operators: >, >=, <, <=, ==, !=
        
        Args:
            left: Left operand
            op: Comparison operator
            right: Right operand
            
        Returns:
            True if comparison is true, False otherwise
        """
        try:
            if op == ">":
                return left > right
            elif op == ">=":
                return left >= right
            elif op == "<":
                return left < right
            elif op == "<=":
                return left <= right
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            else:
                logger.warning(f"Unknown comparison operator: {op}")
                return False
        except (TypeError, ValueError) as e:
            logger.warning(f"Comparison failed: {left} {op} {right} - {e}")
            return False
    
    def _eval_threshold_condition(self, value: float, condition: str) -> bool:
        """
        Evaluate a threshold condition string safely.
        
        Supports: "> 1.5", ">= 1.0", "< 0.5", "<= 0.8", "== 1.0"
        
        Args:
            value: Numeric value to test
            condition: Condition string like "> 1.5"
            
        Returns:
            True if condition is met, False otherwise
        """
        try:
            condition = condition.strip()
            
            if condition.startswith(">="):
                threshold = float(condition[2:].strip())
                return value >= threshold
            elif condition.startswith(">"):
                threshold = float(condition[1:].strip())
                return value > threshold
            elif condition.startswith("<="):
                threshold = float(condition[2:].strip())
                return value <= threshold
            elif condition.startswith("<"):
                threshold = float(condition[1:].strip())
                return value < threshold
            elif condition.startswith("=="):
                threshold = float(condition[2:].strip())
                return value == threshold
            elif condition.startswith("!="):
                threshold = float(condition[2:].strip())
                return value != threshold
            else:
                logger.warning(f"Unknown threshold condition format: {condition}")
                return False
                
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing threshold condition '{condition}': {e}")
            return False


# Global registry instance (lazy-loaded)
_registry_instance: Optional[RuleRegistry] = None


def get_rule_registry(registry_path: Optional[str] = None) -> RuleRegistry:
    """Get or create the global rule registry instance."""
    global _registry_instance
    if _registry_instance is None or registry_path is not None:
        _registry_instance = RuleRegistry(registry_path)
    return _registry_instance


def eval_rules_dynamic(data: NormalizedInput, registry_path: Optional[str] = None) -> List[RuleTrigger]:
    """Evaluate rules using the dynamic registry system."""
    registry = get_rule_registry(registry_path)
    evaluator = RuleEvaluator(registry)
    return evaluator.evaluate_all(data)
