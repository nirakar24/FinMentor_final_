"""
Behavior detection endpoint for identifying financial patterns in irregular income users.
"""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.behavior import BehaviorDetectRequest, BehaviorDetectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/behavior", tags=["Behavior Detection"])


def detect_behavior_flags(request: BehaviorDetectRequest) -> List[str]:
    """
    Pure function: Detect behavioral financial patterns based on rules.
    
    Detection Rules:
    - discretionary_ratio > 0.30 → "high_discretionary_spender"
    - high_spend_days >= 6 → "frequent_high_spend_days"
    - cashflow_stability < 0.6 → "unstable_cashflow"
    - zero_income_days >= 5 → "income_gap_risk"
    - consecutive_deficit_count >= 2 → "recurring_deficit"
    - any large_transaction > avg_daily_expense * 5 → "spike_transaction_behavior"
    
    Args:
        request: BehaviorDetectRequest with user financial data
    
    Returns:
        List of detected behavior flags
    """
    flags = []
    
    # Rule 1: High discretionary spending
    if request.discretionary_ratio > 0.30:
        flags.append("high_discretionary_spender")
    
    # Rule 2: Frequent high spend days
    if request.high_spend_days >= 6:
        flags.append("frequent_high_spend_days")
    
    # Rule 3: Unstable cashflow
    if request.cashflow_stability < 0.6:
        flags.append("unstable_cashflow")
    
    # Rule 4: Income gap risk
    if request.zero_income_days >= 5:
        flags.append("income_gap_risk")
    
    # Rule 5: Recurring deficit
    if request.consecutive_deficit_count >= 2:
        flags.append("recurring_deficit")
    
    # Rule 6: Spike transaction behavior
    spike_threshold = request.avg_daily_expense * 5
    for transaction in request.large_transactions:
        if transaction > spike_threshold:
            flags.append("spike_transaction_behavior")
            break  # Only add flag once
    
    return flags


def calculate_behavior_score(flags: List[str]) -> int:
    """
    Pure function: Calculate behavior risk score from detected flags.
    
    Scoring Logic:
    - Each detected flag = 20 points
    - Cap at 100
    
    Args:
        flags: List of detected behavior flags
    
    Returns:
        Behavior score (0-100)
    """
    score = len(flags) * 20
    return min(score, 100)


def classify_risk_level(score: int) -> str:
    """
    Pure function: Classify risk level from behavior score.
    
    Classification:
    - 0–30 = low
    - 31–60 = medium
    - 61–100 = high
    
    Args:
        score: Behavior score (0-100)
    
    Returns:
        Risk level: "low", "medium", or "high"
    """
    if score <= 30:
        return "low"
    elif score <= 60:
        return "medium"
    else:
        return "high"


@router.post(
    "/detect",
    response_model=BehaviorDetectResponse,
    summary="Detect behavioral financial patterns",
    description="""
    Detects behavioral financial patterns for users with irregular income.
    
    **Detection Rules:**
    - discretionary_ratio > 0.30 → high_discretionary_spender
    - high_spend_days >= 6 → frequent_high_spend_days
    - cashflow_stability < 0.6 → unstable_cashflow
    - zero_income_days >= 5 → income_gap_risk
    - consecutive_deficit_count >= 2 → recurring_deficit
    - any large_transaction > avg_daily_expense * 5 → spike_transaction_behavior
    
    **Scoring:** Each flag = 20 points (max 100)
    
    **Risk Classification:**
    - 0–30 = low
    - 31–60 = medium
    - 61–100 = high
    """,
    responses={
        200: {
            "description": "Behavior detection successful",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "USR_12345",
                        "behavior_flags": [
                            "high_discretionary_spender",
                            "frequent_high_spend_days",
                            "unstable_cashflow",
                            "income_gap_risk"
                        ],
                        "behavior_score": 80,
                        "risk_level": "high",
                        "generated_at": "2025-11-29T12:34:56.789Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid input - numeric values out of range",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "cashflow_stability must be between 0.0 and 1.0"
                    }
                }
            }
        },
        500: {
            "description": "Runtime detection error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Behavior detection error: Internal processing failed"
                    }
                }
            }
        }
    }
)
async def detect_behavior(request: BehaviorDetectRequest) -> BehaviorDetectResponse:
    """
    POST /behavior/detect - Detect behavioral financial patterns.
    
    Args:
        request: BehaviorDetectRequest with user financial metrics
    
    Returns:
        BehaviorDetectResponse with flags, score, and risk level
    
    Raises:
        HTTPException: 400 for validation errors, 500 for runtime errors
    """
    try:
        logger.info(f"[Behavior Detection] Processing user {request.user_id}")
        
        # Detect behavior flags (pure function - testable)
        flags = detect_behavior_flags(request)
        
        # Calculate behavior score (pure function - testable)
        score = calculate_behavior_score(flags)
        
        # Classify risk level (pure function - testable)
        risk_level = classify_risk_level(score)
        
        # Generate timezone-aware ISO 8601 timestamp
        generated_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(
            f"[Behavior Detection] User {request.user_id}: "
            f"{len(flags)} flags, score={score}, risk={risk_level}"
        )
        
        return BehaviorDetectResponse(
            user_id=request.user_id,
            behavior_flags=flags,
            behavior_score=score,
            risk_level=risk_level,
            generated_at=generated_at
        )
    
    except ValueError as ve:
        logger.error(f"[Behavior Detection] Validation error for user {request.user_id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    
    except Exception as e:
        logger.error(f"[Behavior Detection] Runtime error for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Behavior detection error: {str(e)}")
