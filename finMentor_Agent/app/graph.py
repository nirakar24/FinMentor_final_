"""
LangGraph workflow definition for the Financial Coaching Agent.
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.state import FinancialAgentState
from app.tools import (
    fetch_snapshot,
    evaluate_rules,
    detect_behavior,
    generate_advice
)
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


async def fetch_snapshot_node(state: FinancialAgentState) -> Dict[str, Any]:
    """
    Node 1: Fetch user financial snapshot.
    """
    logger.info(f"[Node 1] Fetching snapshot for user: {state.user_id}")
    
    try:
        snapshot = await fetch_snapshot(state.user_id)
        logger.debug(f"Snapshot data: {snapshot}")
        return {"user_snapshot": snapshot}
    except RuntimeError as e:
        logger.error(f"Snapshot fetch failed: {e}")
        return {
            "user_snapshot": {},
            "errors": state.errors + [f"Snapshot fetch failed: {str(e)}"]
        }


async def evaluate_rules_node(state: FinancialAgentState) -> Dict[str, Any]:
    """
    Node 2: Evaluate financial rules based on snapshot.
    """
    logger.info("[Node 2] Evaluating financial rules")
    
    if not state.user_snapshot:
        return {
            "rule_engine_output": {},
            "errors": state.errors + ["No user snapshot available"]
        }
    
    try:
        # Extract required fields from snapshot
        snapshot = state.user_snapshot
        
        # Log snapshot keys for debugging
        logger.debug(f"Snapshot keys: {list(snapshot.keys())}")
        
        # Extract required fields matching /evaluate API spec
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        
        # Extract nested data from snapshot structure
        income_data = snapshot.get("income", {})
        spending_data = snapshot.get("spending", {})
        
        # Get income and expense data from nested structure
        avg_monthly_income = income_data.get("average_monthly", 0.0)
        avg_monthly_expense = spending_data.get("total_monthly", 0.0)
        current_month_income = snapshot.get("current_month_income") or avg_monthly_income
        current_month_expense = snapshot.get("current_month_expense") or avg_monthly_expense
        
        # Ensure positive values for required fields
        if avg_monthly_income <= 0:
            avg_monthly_income = 1.0  # Fallback to avoid API rejection
        if current_month_income <= 0:
            current_month_income = avg_monthly_income
        
        # Build payload matching your API spec
        payload = {
            "user_id": state.user_id,
            "month": current_month,
            "avg_monthly_income": avg_monthly_income,
            "avg_monthly_expense": max(0.0, avg_monthly_expense),
            "current_month_income": current_month_income,
            "current_month_expense": max(0.0, current_month_expense),
            
            # Optional fields from snapshot
            "savings_rate": snapshot.get("savings_rate"),
            "income_volatility": snapshot.get("income_volatility"),
            "risk_level": snapshot.get("risk_level"),
            "Category_spend": snapshot.get("Category_spend"),
            "Behaviour_metrics": snapshot.get("Behaviour_metrics"),
            "Forecast": snapshot.get("Forecast"),
            "persona_type": snapshot.get("persona_type"),
            "confidence_score": snapshot.get("confidence_score"),
            "last_updated": snapshot.get("last_updated"),
            "insights": snapshot.get("insights")
        }
        
        # Remove None values to let API use defaults
        payload = {k: v for k, v in payload.items() if v is not None}
        
        logger.debug(f"Rule engine payload: {payload}")
        
        rule_output = await evaluate_rules(payload)
        return {"rule_engine_output": rule_output}
    except RuntimeError as e:
        logger.error(f"Rule evaluation failed: {e}")
        return {
            "rule_engine_output": {},
            "errors": state.errors + [f"Rule evaluation failed: {str(e)}"]
        }


async def detect_behavior_node(state: FinancialAgentState) -> Dict[str, Any]:
    """
    Node 3: Detect financial behavior patterns.
    """
    logger.info("[Node 3] Detecting behavior patterns")
    
    if not state.user_snapshot:
        return {
            "behavior_output": {},
            "errors": state.errors + ["No snapshot for behavior detection"]
        }
    
    try:
        snapshot = state.user_snapshot
        
        # Extract behavior metrics from nested structure or use spending data
        behavior_metrics = snapshot.get("Behavior_metrics", {})
        spending = snapshot.get("spending", {})
        
        # Calculate metrics from available data
        avg_daily_expense = behavior_metrics.get("avg_daily_expense") or (spending.get("total_monthly", 0) / 30.0)
        discretionary_ratio = behavior_metrics.get("discretionary_ratio") or spending.get("discretionary_ratio", 0.0)
        
        payload = {
            "user_id": state.user_id,
            "avg_daily_expense": avg_daily_expense,
            "high_spend_days": behavior_metrics.get("high_spend_days", 0),
            "cashflow_stability": behavior_metrics.get("cashflow_stability", 0.0),
            "discretionary_ratio": discretionary_ratio
        }
        
        behavior_output = await detect_behavior(payload)
        return {"behavior_output": behavior_output}
    except RuntimeError as e:
        logger.error(f"Behavior detection failed: {e}")
        return {
            "behavior_output": {},
            "errors": state.errors + [f"Behavior detection failed: {str(e)}"]
        }


async def generate_advice_node(state: FinancialAgentState) -> Dict[str, Any]:
    """
    Node 4: Generate personalized financial advice.
    """
    logger.info("[Node 4] Generating financial advice")
    
    if not state.rule_engine_output:
        return {
            "advice_output": {
                "advice": "We could not generate personalized advice right now, but your financial risks have been detected."
            },
            "errors": state.errors + ["Insufficient data for advice generation"]
        }
    
    try:
        # Get persona_type from snapshot (nested in profile)
        snapshot = state.user_snapshot or {}
        profile = snapshot.get("profile", {})
        persona_type = profile.get("persona") or snapshot.get("persona_type", "default")
        
        # Validate persona_type is one of the allowed values
        valid_personas = ["gig_worker", "salaried", "default"]
        if persona_type not in valid_personas:
            logger.warning(f"Invalid persona_type '{persona_type}', defaulting to 'default'")
            persona_type = "default"
        
        # Ensure rules_output has the required structure for advice API
        rules_output = state.rule_engine_output or {}
        
        # Transform rule engine output to match advice API expectations
        if "risk_summary" not in rules_output or "normalized_data" not in rules_output:
            logger.debug("Transforming rules_output to match advice API format")
            
            # Create risk_summary if missing
            risk_summary = rules_output.get("risk_summary", {
                "triggered_rules": rules_output.get("triggered_rules", []),
                "risk_level": rules_output.get("risk_level", "unknown"),
                "risk_score": rules_output.get("risk_score", 0),
                "recommendations": rules_output.get("recommendations", [])
            })
            
            # Create normalized_data from snapshot nested structure
            snapshot = state.user_snapshot or {}
            income_data = snapshot.get("income", {})
            spending_data = snapshot.get("spending", {})
            savings_data = snapshot.get("savings", {})
            
            normalized_data = rules_output.get("normalized_data", {
                "avg_monthly_income": income_data.get("average_monthly", 0),
                "avg_monthly_expense": spending_data.get("total_monthly", 0),
                "current_month_income": income_data.get("average_monthly", 0),
                "current_month_expense": spending_data.get("total_monthly", 0),
                "savings_rate": savings_data.get("monthly_savings_rate", 0),
                "income_volatility": (100 - income_data.get("stability_score", 50)) / 100.0,
                "spending_categories": spending_data.get("categories", [])  # Add spending breakdown for LLM
            })
            
            rules_output = {
                **rules_output,
                "risk_summary": risk_summary,
                "normalized_data": normalized_data
            }
        
        payload = {
            "user_id": state.user_id,
            "rules_output": rules_output,
            "behavior_output": state.behavior_output or {},
            "persona_type": persona_type,
            "user_query": state.user_query  # Pass the user's specific question
        }
        
        logger.debug(f"Advice generation payload: {payload}")
        
        advice = await generate_advice(payload)
        return {"advice_output": advice}
    except RuntimeError as e:
        logger.error(f"Advice generation failed: {e}")
        return {
            "advice_output": {
                "advice": "We could not generate personalized advice right now, but your financial risks have been detected."
            },
            "errors": state.errors + [f"Advice generation failed: {str(e)}"]
        }


async def finalize_node(state: FinancialAgentState) -> Dict[str, Any]:
    """
    Node 5: Format final response for the user.
    """
    logger.info("[Node 5] Finalizing response")
    
    final_output = {
        "user_id": state.user_id,
        "snapshot": state.user_snapshot or {},
        "risk_analysis": state.rule_engine_output or {},
        "behavior": state.behavior_output or {},
        "advice": state.advice_output or {},
        "errors": state.errors
    }
    
    logger.info("Response finalized successfully")
    
    return final_output


def create_financial_agent_graph() -> StateGraph:
    """
    Create and configure the LangGraph workflow for the financial agent.
    
    Returns:
        Configured StateGraph instance
    """
    workflow = StateGraph(FinancialAgentState)
    
    workflow.add_node("fetch_snapshot", fetch_snapshot_node)
    workflow.add_node("evaluate_rules", evaluate_rules_node)
    workflow.add_node("detect_behavior", detect_behavior_node)
    workflow.add_node("generate_advice", generate_advice_node)
    workflow.add_node("finalize", finalize_node)
    
    workflow.set_entry_point("fetch_snapshot")
    workflow.add_edge("fetch_snapshot", "evaluate_rules")
    workflow.add_edge("evaluate_rules", "detect_behavior")
    workflow.add_edge("detect_behavior", "generate_advice")
    workflow.add_edge("generate_advice", "finalize")
    workflow.add_edge("finalize", END)
    
    app = workflow.compile()
    
    logger.info("Financial Agent Graph created successfully")
    
    return app
