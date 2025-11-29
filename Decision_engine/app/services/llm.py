"""
LLM service for generating financial advice using external LLM APIs.

Supports: OpenAI, Azure OpenAI, Groq, Gemini, Ollama (local)
Temperature: ≤ 0.4 for financial stability
Max tokens: ≤ 600
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | azure | groq | gemini | ollama
LLM_API_KEY = os.getenv("LLM_API_KEY")  # MUST be set via environment variable
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "600"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))

# System prompt (MANDATORY template)
SYSTEM_PROMPT = """You are an autonomous financial coach for people with irregular income such as gig workers and vendors.

🎯 CRITICAL: If the user asks a SPECIFIC QUESTION, you MUST answer it DIRECTLY and FIRST in the summary field.

You must generate personalized, practical, conservative financial advice.
You must not hallucinate numbers.
You must only use the values passed in the input.
You must output STRICT JSON in the exact schema provided.
No markdown. No explanation. No prefix. Only valid JSON.

When a user_query is provided:
1. Answer their SPECIFIC question FIRST in the summary
2. Give a clear YES/NO or direct recommendation
3. Provide specific numbers and timeframes
4. Then add general financial health context"""

# Response schema definition for LLM
RESPONSE_SCHEMA = {
    "user_id": "string",
    "summary": "1-2 line financial health summary",
    "top_risks": ["string"],
    "behavioral_warnings": ["string"],
    "action_steps": [
        {
            "title": "string",
            "description": "string",
            "priority": "high | medium | low"
        }
    ],
    "savings_tip": "string",
    "spending_tip": "string",
    "stability_tip": "string",
    "confidence_message": "string",
    "generated_at": "ISO 8601 timestamp"
}


def _build_user_prompt(
    user_id: str,
    rules_output: Dict[str, Any],
    behavior_output: Dict[str, Any],
    persona_type: str,
    user_query: str | None = None
) -> str:
    """
    Build user prompt from structured data.
    
    MUST include:
    - User's specific question (if provided)
    - Top 3 risks
    - All detected behavior flags
    - User persona
    - Emergency fund status
    - Savings ratio
    - Cashflow stability
    - Discretionary spend ratio
    """
    # Extract top risks
    risk_summary = rules_output.get("risk_summary", {})
    top_risks_data = risk_summary.get("top_risks", [])[:3]
    top_risks = [r.get("summary", r.get("dimension", "Unknown risk")) for r in top_risks_data]
    total_risk_score = risk_summary.get("total_risk_score", 0)
    weighted_severity = risk_summary.get("weighted_severity", "unknown")
    
    # Extract behavior data
    behavior_flags = behavior_output.get("behavior_flags", [])
    behavior_score = behavior_output.get("behavior_score", 0)
    behavior_risk = behavior_output.get("risk_level", "unknown")
    
    # Extract normalized data
    normalized = rules_output.get("normalized_data", {})
    emergency_fund = normalized.get("emergency_fund_balance", 0)
    monthly_income = normalized.get("current_month_income", 0)
    savings_rate = normalized.get("savings_rate", 0)
    
    # Calculate emergency fund coverage
    avg_expense = normalized.get("avg_monthly_expense", 1)
    emergency_months = round(emergency_fund / avg_expense, 1) if avg_expense > 0 else 0
    
    # Extract behavior metrics
    behavior_metrics = normalized.get("behavior_metrics", {})
    cashflow_stability = behavior_metrics.get("cashflow_stability", 0)
    discretionary_ratio = behavior_metrics.get("discretionary_ratio", 0)
    
    # Extract spending categories (CRITICAL for LLM context)
    spending_categories = normalized.get("spending_categories", [])
    if not spending_categories:
        # Try alternate location in category_spend
        category_spend = normalized.get("category_spend", {})
        if category_spend:
            total_spend = sum(category_spend.values())
            spending_categories = [
                {
                    "category": cat,
                    "amount": amt,
                    "percentage": (amt / total_spend * 100) if total_spend > 0 else 0
                }
                for cat, amt in category_spend.items()
            ]
    
    # Build spending breakdown text
    spending_breakdown = ""
    if spending_categories:
        spending_breakdown = "\n".join([
            f"  - {cat.get('category', 'Unknown')}: ₹{cat.get('amount', 0):,.0f} ({cat.get('percentage', 0):.1f}%)"
            for cat in spending_categories
        ])
    else:
        spending_breakdown = "  Not available"
    
    # Build user query section
    query_section = ""
    if user_query:
        query_section = f"""
🎯 USER'S SPECIFIC QUESTION (ANSWER THIS FIRST!):
"{user_query}"

⚠️ CRITICAL: Your summary MUST directly answer this question with:
- Clear YES/NO or specific recommendation
- Exact numbers and timeframes from the data below
- Reasoning based on their financial situation
"""
    else:
        query_section = "USER QUESTION: None provided - give general financial health assessment"
    
    prompt = f"""
USER_ID: {user_id}
PERSONA: {persona_type.upper()}

{query_section}

=== RISK ASSESSMENT ===
Total Risk Score: {total_risk_score}/100
Weighted Severity: {weighted_severity}
Top 3 Risks:
{chr(10).join(f"  {i+1}. {risk}" for i, risk in enumerate(top_risks)) if top_risks else "  None"}

=== BEHAVIORAL ANALYSIS ===
Behavior Score: {behavior_score}/100
Behavior Risk: {behavior_risk}
Detected Flags:
{chr(10).join(f"  - {flag}" for flag in behavior_flags) if behavior_flags else "  None"}

=== FINANCIAL METRICS ===
Monthly Income: ₹{monthly_income:,.0f}
Monthly Expenses: ₹{avg_expense:,.0f}
Emergency Fund Coverage: {emergency_months} months (Balance: ₹{emergency_fund:,.0f})
Savings Rate: {savings_rate*100:.1f}%
Cashflow Stability: {cashflow_stability*100:.1f}%
Discretionary Ratio: {discretionary_ratio*100:.1f}%

=== SPENDING BREAKDOWN (USE THESE REAL NUMBERS!) ===
{spending_breakdown}

=== CRITICAL INSTRUCTIONS ===
1. 🚨 USE THE ACTUAL SPENDING AMOUNTS ABOVE - DO NOT make up or hallucinate numbers like "₹0"
2. 🚨 When mentioning spending categories (Food, Transport, etc.), use the EXACT amounts from SPENDING BREAKDOWN
3. Generate advice tailored for {persona_type} persona
4. If persona is "gig_worker", emphasize variable-income strategies
5. Provide 2-4 action steps with HIGH priority for top risks
6. ALL numeric values MUST come from the data above - verify before outputting
8. Output MUST be valid JSON matching this schema:
{json.dumps(RESPONSE_SCHEMA, indent=2)}

9. Set generated_at to current UTC time in ISO 8601 format
10. NO MARKDOWN, NO EXPLANATIONS - ONLY JSON
"""
    return prompt.strip()


def _generate_spending_tip(spending_categories: list, avg_expense: float) -> str:
    """Generate spending tip based on actual spending categories."""
    if not spending_categories:
        return "Reduce non-essential expenses by 15% and redirect to savings"
    
    # Find highest discretionary categories
    discretionary = ["Entertainment", "Shopping", "Dining", "Subscriptions", "Others"]
    high_spend = [
        cat for cat in spending_categories 
        if cat.get("category") in discretionary and cat.get("percentage", 0) > 10
    ]
    
    if high_spend:
        top_cat = high_spend[0]
        category_name = top_cat.get("category", "discretionary")
        amount = top_cat.get("amount", 0)
        reduction = amount * 0.15
        return f"Reduce {category_name} spending from ₹{amount:,.0f} by 15% (save ₹{reduction:,.0f}/month)"
    
    # Generic advice with real numbers
    total_spend = sum(cat.get("amount", 0) for cat in spending_categories)
    if total_spend > 0:
        reduction = total_spend * 0.10
        return f"Review all categories and reduce total spending by 10% to save ₹{reduction:,.0f}/month"
    
    return "Track expenses and identify areas to reduce spending by 10-15%"


def _get_fallback_advice(
    user_id: str,
    rules_output: Dict[str, Any],
    behavior_output: Dict[str, Any],
    persona_type: str,
    user_query: str | None = None
) -> Dict[str, Any]:
    """
    Template-based fallback advice when LLM is unavailable.
    """
    logger.warning(f"Using fallback advice for user {user_id}" + (f" - Query: '{user_query}'" if user_query else ""))
    
    risk_summary = rules_output.get("risk_summary", {})
    top_risks = risk_summary.get("top_risks", [])[:3]
    behavior_flags = behavior_output.get("behavior_flags", [])
    behavior_score = behavior_output.get("behavior_score", 0)
    
    # Extract financial metrics for query-specific advice
    normalized = rules_output.get("normalized_data", {})
    emergency_fund = normalized.get("emergency_fund_balance", 0)
    avg_expense = normalized.get("avg_monthly_expense", 1)
    emergency_months = round(emergency_fund / avg_expense, 1) if avg_expense > 0 else 0
    savings_rate = normalized.get("savings_rate", 0)
    monthly_income = normalized.get("current_month_income", 0)
    
    # Extract spending categories for better advice
    spending_categories = normalized.get("spending_categories", [])
    if not spending_categories:
        category_spend = normalized.get("category_spend", {})
        if category_spend:
            total_spend = sum(category_spend.values())
            spending_categories = [
                {
                    "category": cat,
                    "amount": amt,
                    "percentage": (amt / total_spend * 100) if total_spend > 0 else 0
                }
                for cat, amt in category_spend.items()
            ]
    
    # Build fallback response
    top_risk_summaries = [r.get("summary", "Financial risk detected") for r in top_risks]
    
    persona_advice = {
        "gig_worker": {
            "stability": "Build a 6-month emergency fund to handle income gaps between gigs",
            "savings": "Save 25% of high-income months to cover low-income periods"
        },
        "salaried": {
            "stability": "Maintain consistent savings with automated transfers",
            "savings": "Target 20% savings rate with employer benefits"
        },
        "default": {
            "stability": "Track daily expenses to identify spending patterns",
            "savings": "Start with a 10% savings goal and increase gradually"
        }
    }
    
    persona_tips = persona_advice.get(persona_type, persona_advice["default"])
    
    # Generate query-specific summary if user asked a question
    if user_query:
        query_lower = user_query.lower()
        if "vacation" in query_lower or "trip" in query_lower or "travel" in query_lower:
            if emergency_months < 1:
                summary = f"❌ Regarding '{user_query}': Not recommended. Your emergency fund covers only {emergency_months} months. Build at least 1 month's buffer first."
            elif emergency_months < 3 and savings_rate < 0.15:
                summary = f"⚠️ Regarding '{user_query}': Only if it's a low-cost trip (<₹5,000). Your emergency fund ({emergency_months} months) and savings rate ({savings_rate*100:.0f}%) are below targets."
            else:
                summary = f"✅ Regarding '{user_query}': You can afford a modest vacation if budgeted carefully. Keep it under {avg_expense * 0.2:.0f} to maintain financial stability."
        elif "buy" in query_lower or "purchase" in query_lower or "phone" in query_lower or "laptop" in query_lower:
            if emergency_months < 1:
                summary = f"❌ Regarding '{user_query}': Not recommended. Build your emergency fund to 1 month ({avg_expense:.0f}) first. Current: {emergency_months} months."
            else:
                summary = f"⚠️ Regarding '{user_query}': Consider if it's essential. Your emergency fund is {emergency_months} months (target: 3+). Budget max {avg_expense * 0.3:.0f} for non-essentials."
        elif "save" in query_lower or "saving" in query_lower:
            target_savings = avg_expense * 0.20
            summary = f"💰 Regarding '{user_query}': Target saving ₹{target_savings:.0f}/month (20% of expenses). Current rate: {savings_rate*100:.0f}%. Focus on building 3-month emergency fund first."
        else:
            summary = f"📋 Regarding '{user_query}': Based on your financial health (score: {behavior_score}/100, emergency fund: {emergency_months} months), review the recommendations below for guidance."
    else:
        summary = f"Behavior score: {behavior_score}/100. Emergency fund: {emergency_months} months. Review detected patterns and take action."
    
    return {
        "user_id": user_id,
        "summary": summary,
        "top_risks": top_risk_summaries or ["Review your financial data for anomalies"],
        "behavioral_warnings": behavior_flags or ["No critical behavioral warnings detected"],
        "action_steps": [
            {
                "title": "Review your budget",
                "description": "Analyze spending patterns and identify optimization areas",
                "priority": "high"
            },
            {
                "title": "Build emergency savings",
                "description": "Target 3-6 months of expenses in liquid savings",
                "priority": "high"
            }
        ],
        "savings_tip": persona_tips["savings"],
        "spending_tip": _generate_spending_tip(spending_categories, avg_expense),
        "stability_tip": persona_tips["stability"],
        "confidence_message": "Consistent small actions lead to financial stability. Start today.",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


async def generate_advice_with_llm(
    user_id: str,
    rules_output: Dict[str, Any],
    behavior_output: Dict[str, Any],
    persona_type: str,
    user_query: str | None = None
) -> Dict[str, Any]:
    """
    Generate financial advice using LLM with fallback handling.
    
    Args:
        user_query: User's specific financial question (e.g., "Can I go on vacation?")
    
    Returns:
        Dict matching AdviceGenerateResponse schema
    
    Raises:
        Exception: If LLM call fails AND fallback is disabled
    """
    try:
        # Build prompt with user query
        user_prompt = _build_user_prompt(user_id, rules_output, behavior_output, persona_type, user_query)
        
        logger.info(f"[LLM] Generating advice for user {user_id} with {LLM_PROVIDER}" + (f" - Query: '{user_query}'" if user_query else ""))
        
        # Check if API key is configured
        if not LLM_API_KEY:
            logger.warning(f"[LLM] No API key configured - using fallback for user {user_id}")
            return _get_fallback_advice(user_id, rules_output, behavior_output, persona_type, user_query)
        
        # Call LLM based on provider
        if LLM_PROVIDER == "openai":
            result = await _call_openai(user_prompt)
        elif LLM_PROVIDER == "azure":
            result = await _call_azure_openai(user_prompt)
        elif LLM_PROVIDER == "groq":
            result = await _call_groq(user_prompt)
        elif LLM_PROVIDER == "gemini":
            result = await _call_gemini(user_prompt)
        elif LLM_PROVIDER == "ollama":
            result = await _call_ollama(user_prompt)
        else:
            logger.warning(f"[LLM] Unknown provider {LLM_PROVIDER} - using fallback")
            return _get_fallback_advice(user_id, rules_output, behavior_output, persona_type, user_query)
        
        # Parse and validate JSON response
        try:
            advice_json = json.loads(result)
            logger.info(f"[LLM] Successfully generated advice for user {user_id}")
            return advice_json
        except json.JSONDecodeError as je:
            logger.error(f"[LLM] Invalid JSON from LLM: {je}")
            
            # Retry once with guard prompt
            logger.info(f"[LLM] Retrying with JSON fix guard for user {user_id}")
            guard_prompt = f"{user_prompt}\n\nIMPORTANT: Your previous response was invalid JSON. Output ONLY valid JSON matching the schema. No markdown, no text."
            
            if LLM_PROVIDER == "openai":
                retry_result = await _call_openai(guard_prompt)
            elif LLM_PROVIDER == "azure":
                retry_result = await _call_azure_openai(guard_prompt)
            elif LLM_PROVIDER == "groq":
                retry_result = await _call_groq(guard_prompt)
            elif LLM_PROVIDER == "gemini":
                retry_result = await _call_gemini(guard_prompt)
            elif LLM_PROVIDER == "ollama":
                retry_result = await _call_ollama(guard_prompt)
            else:
                raise Exception("Unknown provider on retry")
            
            try:
                advice_json = json.loads(retry_result)
                logger.info(f"[LLM] Retry successful for user {user_id}")
                return advice_json
            except json.JSONDecodeError:
                logger.error(f"[LLM] Retry failed - using fallback for user {user_id}")
                return _get_fallback_advice(user_id, rules_output, behavior_output, persona_type, user_query)
    
    except Exception as e:
        logger.error(f"[LLM] Error generating advice for user {user_id}: {e}")
        # Graceful degradation with template-based advice
        return _get_fallback_advice(user_id, rules_output, behavior_output, persona_type, user_query)


async def _call_openai(user_prompt: str) -> str:
    """Call OpenAI API (ChatGPT)"""
    import httpx
    
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(
            f"{LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_azure_openai(user_prompt: str) -> str:
    """Call Azure OpenAI API"""
    import httpx
    
    # Azure uses api-key header instead of Authorization
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(
            f"{LLM_API_BASE}/openai/deployments/{LLM_MODEL}/chat/completions?api-version=2024-02-01",
            headers={
                "api-key": LLM_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_groq(user_prompt: str) -> str:
    """Call Groq API (compatible with OpenAI format)"""
    import httpx
    
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(
            f"{LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_gemini(user_prompt: str) -> str:
    """Call Google Gemini API"""
    import httpx
    
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        # Gemini uses different endpoint structure
        url = f"{LLM_API_BASE}/v1beta/models/{LLM_MODEL}:generateContent?key={LLM_API_KEY}"
        response = await client.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{
                        "text": f"{SYSTEM_PROMPT}\n\n{user_prompt}"
                    }]
                }],
                "generationConfig": {
                    "temperature": LLM_TEMPERATURE,
                    "maxOutputTokens": LLM_MAX_TOKENS,
                    "responseMimeType": "application/json"
                }
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def _call_ollama(user_prompt: str) -> str:
    """Call Ollama (local LLM)"""
    import httpx
    
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        response = await client.post(
            f"{LLM_API_BASE}/api/chat",
            headers={"Content-Type": "application/json"},
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS
                },
                "format": "json"
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
