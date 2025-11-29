from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import traceback
from pydantic import BaseModel, Field

from engine.engine import evaluate_payload
from app.api.behavior import router as behavior_router
from app.api.advice import router as advice_router

APP_VERSION = "1.0.0"


# Snapshot Response Models
class SpendingCategory(BaseModel):
    category: str
    amount: float
    percentage: float


class IncomeStream(BaseModel):
    source: str
    amount: float
    frequency: str


class FinancialSnapshot(BaseModel):
    user_id: str
    profile: Dict[str, Any]
    income: Dict[str, Any]
    spending: Dict[str, Any]
    savings: Dict[str, Any]
    debt: Dict[str, Any]
    financial_health_score: int = Field(..., ge=0, le=100)
    alerts: List[str]
    timestamp: str

app = FastAPI(
    title="Decision Engine",
    version=APP_VERSION,
    description="""
    Financial Decision Engine for Irregular Income Users
    
    **Features:**
    - Rule-based evaluation engine with 30+ dynamic rules
    - Weighted risk scoring across 7 dimensions
    - Behavioral pattern detection for gig workers and vendors
    - LLM-powered personalized financial advice
    - Smart recommendations with parameter injection
    
    **Endpoints:**
    - `/health` - Health check
    - `/evaluate` - Rule engine evaluation
    - `/demo` - Demo with sample data
    - `/behavior/detect` - Behavioral pattern detection
    - `/advice/generate` - LLM-powered advice generation
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:5173",
]

# Register new routers
app.include_router(behavior_router)
app.include_router(advice_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "engine_version": APP_VERSION}


@app.post("/evaluate")
def evaluate(data: Dict[str, Any]):
    try:
        result = evaluate_payload(data)
        return JSONResponse(content=result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")


@app.get("/demo")
def demo():
    try:
        sample_path = Path(__file__).resolve().parents[1] / "sample.json"
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="sample.json not found")
        with open(sample_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        result = evaluate_payload(payload)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Demo error: {str(e)}")


# Dummy Snapshot Data for Hackathon Demo
DUMMY_SNAPSHOTS: Dict[str, Dict[str, Any]] = {
    "GIG_001": {
        "user_id": "GIG_001",
        "profile": {
            "name": "Rajesh Kumar",
            "persona": "gig_worker",
            "age": 28,
            "location": "Mumbai"
        },
        "income": {
            "monthly_streams": [
                {"source": "Uber/Ola Driving", "amount": 35000, "frequency": "weekly"},
                {"source": "Food Delivery", "amount": 12000, "frequency": "daily"},
                {"source": "Freelance Graphic Design", "amount": 8000, "frequency": "sporadic"}
            ],
            "average_monthly": 55000,
            "stability_score": 42
        },
        "spending": {
            "total_monthly": 48000,
            "categories": [
                {"category": "Housing", "amount": 15000, "percentage": 31.25},
                {"category": "Food", "amount": 12000, "percentage": 25.0},
                {"category": "Transportation", "amount": 8000, "percentage": 16.67},
                {"category": "Utilities", "amount": 3000, "percentage": 6.25},
                {"category": "Entertainment", "amount": 5000, "percentage": 10.42},
                {"category": "Others", "amount": 5000, "percentage": 10.42}
            ],
            "discretionary_ratio": 0.31
        },
        "savings": {
            "current_balance": 12000,
            "emergency_fund_months": 0.22,
            "monthly_savings_rate": 0.13
        },
        "debt": {
            "total_outstanding": 45000,
            "monthly_emi": 3500,
            "types": ["Personal Loan", "Credit Card"]
        },
        "financial_health_score": 38,
        "alerts": [
            "🚨 Critical: Emergency fund below 1 month",
            "⚠️ High income volatility detected",
            "⚠️ Debt-to-income ratio exceeds 60%",
            "💡 Consider reducing discretionary spending"
        ]
    },
    "VEN_001": {
        "user_id": "VEN_001",
        "profile": {
            "name": "Meera Devi",
            "persona": "informal_vendor",
            "age": 35,
            "location": "Delhi"
        },
        "income": {
            "monthly_streams": [
                {"source": "Street Food Stall", "amount": 28000, "frequency": "daily"},
                {"source": "Catering Orders", "amount": 6000, "frequency": "sporadic"}
            ],
            "average_monthly": 34000,
            "stability_score": 55
        },
        "spending": {
            "total_monthly": 31000,
            "categories": [
                {"category": "Housing", "amount": 10000, "percentage": 32.26},
                {"category": "Food", "amount": 8000, "percentage": 25.81},
                {"category": "Business Expenses", "amount": 7000, "percentage": 22.58},
                {"category": "Utilities", "amount": 2500, "percentage": 8.06},
                {"category": "Healthcare", "amount": 2000, "percentage": 6.45},
                {"category": "Others", "amount": 1500, "percentage": 4.84}
            ],
            "discretionary_ratio": 0.15
        },
        "savings": {
            "current_balance": 25000,
            "emergency_fund_months": 0.81,
            "monthly_savings_rate": 0.09
        },
        "debt": {
            "total_outstanding": 15000,
            "monthly_emi": 1500,
            "types": ["Microfinance Loan"]
        },
        "financial_health_score": 52,
        "alerts": [
            "⚠️ Emergency fund below recommended 3 months",
            "✅ Good control on discretionary spending",
            "💡 Consider increasing savings rate to 15%"
        ]
    },
    "SAL_001": {
        "user_id": "SAL_001",
        "profile": {
            "name": "Ankit Sharma",
            "persona": "salaried",
            "age": 32,
            "location": "Bangalore"
        },
        "income": {
            "monthly_streams": [
                {"source": "Salary (IT Company)", "amount": 75000, "frequency": "monthly"},
                {"source": "Freelance Consulting", "amount": 10000, "frequency": "monthly"}
            ],
            "average_monthly": 85000,
            "stability_score": 92
        },
        "spending": {
            "total_monthly": 62000,
            "categories": [
                {"category": "Housing", "amount": 25000, "percentage": 40.32},
                {"category": "Food", "amount": 12000, "percentage": 19.35},
                {"category": "Transportation", "amount": 8000, "percentage": 12.90},
                {"category": "Utilities", "amount": 4000, "percentage": 6.45},
                {"category": "Entertainment", "amount": 6000, "percentage": 9.68},
                {"category": "Healthcare", "amount": 3000, "percentage": 4.84},
                {"category": "Others", "amount": 4000, "percentage": 6.45}
            ],
            "discretionary_ratio": 0.18
        },
        "savings": {
            "current_balance": 180000,
            "emergency_fund_months": 2.90,
            "monthly_savings_rate": 0.27
        },
        "debt": {
            "total_outstanding": 350000,
            "monthly_emi": 12000,
            "types": ["Home Loan", "Car Loan"]
        },
        "financial_health_score": 71,
        "alerts": [
            "⚠️ Emergency fund slightly below 3 months target",
            "✅ Excellent savings rate",
            "✅ Good income stability",
            "💡 Consider debt consolidation to reduce EMI burden"
        ]
    }
}


@app.get("/snapshot/{user_id}", response_model=Dict[str, Any])
def get_snapshot(user_id: str):
    """
    Get financial snapshot for a demo user (Hackathon Demo Purpose).
    
    Available demo users:
    - GIG_001: High-volatility gig worker
    - VEN_001: Informal street vendor
    - SAL_001: Stable salaried employee
    """
    from datetime import datetime
    
    if user_id not in DUMMY_SNAPSHOTS:
        raise HTTPException(
            status_code=404, 
            detail=f"User '{user_id}' not found. Available: GIG_001, VEN_001, SAL_001"
        )
    
    snapshot = DUMMY_SNAPSHOTS[user_id].copy()
    snapshot["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    return snapshot
