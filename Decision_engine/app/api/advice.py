"""
LLM-powered financial advice generation endpoint.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.schemas.advice import (
    AdviceGenerateRequest,
    AdviceGenerateResponse,
    ActionStep
)
from app.services.llm import generate_advice_with_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advice", tags=["Advice Generation"])


@router.post(
    "/generate",
    response_model=AdviceGenerateResponse,
    summary="Generate LLM-powered financial advice",
    description="""
    Generates natural-language financial advice using an external LLM based on:
    - Rule engine output from /evaluate
    - Behavior detection output from /behavior/detect
    - User income persona (gig_worker, salaried, or default)
    - **User's specific question (user_query)** - e.g., "Can I afford a vacation?", "Should I buy a new phone?"
    
    **⚠️ CRITICAL: If user_query is provided, the summary will DIRECTLY answer the question with specific numbers and recommendations.**
    
    **LLM Configuration:**
    - Temperature ≤ 0.4 for financial stability
    - Max tokens ≤ 600
    - Strict JSON output only
    - No hallucinated numbers
    
    **Supported LLM Providers:**
    - OpenAI (GPT-4, GPT-3.5)
    - Azure OpenAI
    - Groq
    - Google Gemini
    - Ollama (local)
    
    **Environment Variables:**
    - LLM_PROVIDER (openai|azure|groq|gemini|ollama)
    - LLM_API_KEY (required for cloud providers)
    - LLM_API_BASE (API endpoint URL)
    - LLM_MODEL (model name/deployment)
    - LLM_TEMPERATURE (default: 0.3)
    - LLM_MAX_TOKENS (default: 600)
    
    **Fallback Behavior:**
    - If LLM unavailable → template-based advice
    - If JSON invalid → retry once with guard prompt
    - If retry fails → template-based advice
    
    **Persona-Specific Advice:**
    - gig_worker: Variable-income specific strategies
    - salaried: Consistent savings with employer benefits
    - default: General financial advice
    """,
    responses={
        200: {
            "description": "Advice generation successful",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "USR_12345",
                        "summary": "❌ Regarding 'Can I go on vacation?': Not recommended right now. With only ₹12,000 in savings (0.22 months emergency fund) and ₹45,000 debt, you lack financial buffer for discretionary travel. Build emergency fund to ₹48,000 first (1 month expenses), then consider a budget trip under ₹5,000.",
                        "top_risks": [
                            "Insufficient emergency fund (0.22 months vs 3 month target)",
                            "High debt-to-income ratio (82%)",
                            "Low savings rate (13% vs 20% target)"
                        ],
                        "behavioral_warnings": [
                            "Discretionary spending exceeds 30% threshold",
                            "Cashflow stability below 60%"
                        ],
                        "action_steps": [
                            {
                                "title": "Build 3-month emergency buffer",
                                "description": "Save ₹15,000 per month to reach ₹45,000 safety net",
                                "priority": "high"
                            },
                            {
                                "title": "Reduce discretionary spending",
                                "description": "Cut non-essential expenses by 20% - start with subscription audit",
                                "priority": "high"
                            }
                        ],
                        "savings_tip": "Automate 20% of variable income into a separate account immediately upon receipt",
                        "spending_tip": "Cut discretionary expenses by 15% - focus on subscription audits",
                        "stability_tip": "Track daily expenses to identify patterns during high-income periods",
                        "confidence_message": "Small consistent actions compound. You can stabilize your finances in 90 days.",
                        "generated_at": "2025-11-29T12:34:56.789Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request - missing required fields",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "rules_output must contain risk_summary"
                    }
                }
            }
        },
        500: {
            "description": "LLM failure or internal error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "LLM service error: Connection timeout after retry"
                    }
                }
            }
        }
    }
)
async def generate_advice(request: AdviceGenerateRequest) -> AdviceGenerateResponse:
    """
    POST /advice/generate - Generate LLM-powered financial advice.
    
    This endpoint calls an external LLM (OpenAI/Azure/Groq/Gemini/Ollama) to generate
    personalized financial advice based on rule engine output and behavior detection.
    
    Args:
        request: AdviceGenerateRequest with rules_output, behavior_output, and persona
    
    Returns:
        AdviceGenerateResponse with structured financial advice
    
    Raises:
        HTTPException: 400 for validation errors, 500 for LLM service errors
    """
    try:
        logger.info(
            f"[Advice Generation] Processing user {request.user_id} "
            f"with persona {request.persona_type}"
        )
        
        # Validate required fields in rules_output
        if "risk_summary" not in request.rules_output:
            raise ValueError("rules_output must contain 'risk_summary' field")
        
        if "normalized_data" not in request.rules_output:
            raise ValueError("rules_output must contain 'normalized_data' field")
        
        # Validate required fields in behavior_output
        if "behavior_flags" not in request.behavior_output:
            raise ValueError("behavior_output must contain 'behavior_flags' field")
        
        if "behavior_score" not in request.behavior_output:
            raise ValueError("behavior_output must contain 'behavior_score' field")
        
        # Call LLM service (async, with fallback handling)
        advice_data = await generate_advice_with_llm(
            user_id=request.user_id,
            rules_output=request.rules_output,
            behavior_output=request.behavior_output,
            persona_type=request.persona_type,
            user_query=request.user_query
        )
        
        # Validate LLM response using Pydantic
        try:
            response = AdviceGenerateResponse(**advice_data)
            
            logger.info(
                f"[Advice Generation] Successfully generated advice for user {request.user_id}: "
                f"{len(response.action_steps)} action steps, "
                f"{len(response.top_risks)} risks identified"
            )
            
            return response
        
        except ValidationError as ve:
            logger.error(f"[Advice Generation] LLM output validation failed for user {request.user_id}: {ve}")
            raise HTTPException(
                status_code=500,
                detail=f"LLM output validation error: {str(ve)}"
            )
    
    except ValueError as ve:
        logger.error(f"[Advice Generation] Validation error for user {request.user_id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        logger.error(f"[Advice Generation] Unexpected error for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Advice generation error: {str(e)}"
        )
