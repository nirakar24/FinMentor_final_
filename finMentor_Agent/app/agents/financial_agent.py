"""
Financial Agent orchestrator for running the LangGraph workflow.
"""
from typing import Optional
from app.graph import create_financial_agent_graph
from app.state import FinancialAgentState, AgentInput, AgentOutput
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


class FinancialAgent:
    """
    Main orchestrator for the Financial Coaching Agent.
    
    This class manages the LangGraph workflow execution and provides
    a clean interface for running financial coaching sessions.
    """
    
    def __init__(self):
        """Initialize the Financial Agent with the compiled graph."""
        self.graph = create_financial_agent_graph()
        logger.info("Financial Agent initialized")
    
    async def run(
        self,
        user_id: str,
        user_query: Optional[str] = None
    ) -> AgentOutput:
        """
        Run the financial coaching workflow for a user.
        
        Args:
            user_id: Unique identifier for the user
            user_query: Optional specific question from the user
        
        Returns:
            AgentOutput containing the final response and analysis
        
        Example:
            >>> agent = FinancialAgent()
            >>> result = await agent.run(
            ...     user_id="12345",
            ...     user_query="How can I reduce my debt?"
            ... )
            >>> print(result.final_response)
        """
        logger.info(f"Starting financial coaching session for user: {user_id}")
        
        # Create initial state
        initial_state = FinancialAgentState(
            user_id=user_id,
            user_query=user_query
        )
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state.model_dump())
            
            logger.info(f"Financial coaching session completed for user: {user_id}")
            
            # Return the final state dict directly (from finalize_node)
            return final_state
        
        except Exception as e:
            logger.error(f"Error running financial agent: {e}", exc_info=True)
            
            # Return error output
            return {
                "user_id": user_id,
                "snapshot": {},
                "risk_analysis": {},
                "behavior": {},
                "advice": {},
                "errors": [str(e)]
            }
    
    async def process(
        self,
        user_id: str,
        user_query: Optional[str] = None
    ):
        """
        Process user request (alias for run method).
        
        Args:
            user_id: Unique identifier for the user
            user_query: Optional specific question from the user
        
        Returns:
            Dict containing the final response and analysis
        """
        return await self.run(user_id=user_id, user_query=user_query)
    
    async def run_from_input(self, agent_input: AgentInput):
        """
        Run the agent using an AgentInput object.
        
        Args:
            agent_input: Structured input containing user_id and optional query
        
        Returns:
            Dict containing the final response and analysis
        """
        return await self.run(
            user_id=agent_input.user_id,
            user_query=agent_input.user_query
        )
