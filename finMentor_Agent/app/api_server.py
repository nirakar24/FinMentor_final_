"""
FastAPI server wrapping the LangGraph Financial Agent.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.agents.financial_agent import FinancialAgent
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Financial Coaching Agent API",
    version="1.0.0",
    description="LangGraph-powered financial coaching agent with production API integration"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request model
class AgentRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    query: Optional[str] = Field(None, description="Optional specific financial question from the user")


# Initialize agent globally
agent = FinancialAgent()
logger.info("Financial Agent initialized for API server")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/agent/run")
async def run_agent(req: AgentRequest):
    """
    Run the financial coaching agent for a user.
    
    Args:
        req: AgentRequest containing user_id and optional query
    
    Returns:
        Complete analysis and advice from the agent
    """
    try:
        logger.info(f"API request received for user: {req.user_id}")
        
        # Call existing agent logic
        result = await agent.run(user_id=req.user_id, user_query=req.query)
        
        logger.debug(f"Agent result keys: {list(result.keys())}")
        logger.debug(f"Agent result: {result}")
        
        # LangGraph returns the state, not finalize_node output
        # State fields: user_id, user_query, user_snapshot, rule_engine_output, behavior_output, advice_output, errors
        user_id = result.get("user_id", req.user_id)
        snapshot = result.get("user_snapshot", {})  # State uses user_snapshot
        rules_output = result.get("rule_engine_output", {})  # State uses rule_engine_output
        behavior_output = result.get("behavior_output", {})  # State uses behavior_output
        advice = result.get("advice_output", {})  # State uses advice_output
        errors = result.get("errors", [])
        
        # Extract action items from advice
        action_items = []
        if advice and advice.get("action_steps"):
            action_items = [
                {
                    "title": step.get("title", ""),
                    "description": step.get("description", ""),
                    "priority": step.get("priority", "medium")
                }
                for step in advice.get("action_steps", [])
            ]
        
        # Create final response summary
        final_response = None
        if advice and advice.get("summary"):
            final_response = advice["summary"]
        
        response = {
            "user_id": user_id,
            "snapshot": snapshot,
            "rules_output": rules_output,
            "behavior_output": behavior_output,
            "advice": advice,
            "final_response": final_response,
            "action_items": action_items,
            "errors": errors
        }
        
        logger.info(f"API request completed successfully for user: {req.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing agent request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process agent request: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
