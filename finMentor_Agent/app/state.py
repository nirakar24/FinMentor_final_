"""
State schema for the Financial Coaching Agent LangGraph.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FinancialAgentState(BaseModel):
    """
    State schema for the financial coaching agent graph.
    
    This state is passed through all nodes in the LangGraph workflow.
    Each node reads from and updates this shared state.
    """
    
    # Input
    user_id: str = Field(
        description="Unique identifier for the user requesting financial advice"
    )
    user_query: Optional[str] = Field(
        default=None,
        description="Optional specific question from the user"
    )
    
    # Intermediate states
    user_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Financial snapshot data from Snapshot API"
    )
    
    rule_engine_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Rule evaluation results from Rule Engine API"
    )
    
    behavior_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Behavioral analysis from Behavior Detection API"
    )
    
    advice_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generated financial advice from Advice Generator API"
    )
    
    # Error tracking
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered during processing"
    )
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class AgentInput(BaseModel):
    """Input schema for the financial agent."""
    
    user_id: str = Field(
        description="Unique identifier for the user"
    )
    user_query: Optional[str] = Field(
        default=None,
        description="Optional specific question from the user"
    )


class AgentOutput(BaseModel):
    """Output schema for the financial agent."""
    
    user_id: str
    final_response: str
    snapshot_summary: Optional[Dict[str, Any]] = None
    rules_triggered: Optional[List[Dict[str, Any]]] = None
    behavior_patterns: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[str]] = None
    errors: List[str] = Field(default_factory=list)
