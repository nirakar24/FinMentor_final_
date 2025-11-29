"""
Main entry point for the Financial Coaching Agent.

This script demonstrates how to run the LangGraph agent from the terminal.
"""
import asyncio
import sys
from app.agents import FinancialAgent
from app.utils.logger import setup_logger
from app.config import settings


logger = setup_logger(__name__)


async def main():
    """
    Main function to run a demo financial coaching session.
    """
    print("=" * 70)
    print("🤖 Financial Coaching Agent - Demo")
    print("=" * 70)
    print()
    
    # Configuration info
    print(f"📋 Configuration:")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   Behavior Detection: {'Enabled' if settings.enable_behavior_detection else 'Disabled'}")
    print(f"   Log Level: {settings.log_level}")
    print()
    
    # Get user input
    try:
        user_id = input("👤 Enter User ID (or press Enter for demo user '12345'): ").strip()
        if not user_id:
            user_id = "12345"
        
        print()
        user_query = input("💬 Enter your financial question (optional, press Enter to skip): ").strip()
        if not user_query:
            user_query = None
        
        print()
        print("🔄 Processing your request...")
        print()
        
        # Initialize and run the agent
        agent = FinancialAgent()
        result = await agent.run(user_id=user_id, user_query=user_query)
        
        # Display results
        print()
        print("=" * 70)
        print(f"📊 FINANCIAL ANALYSIS FOR USER: {result.get('user_id', 'N/A')}")
        print("=" * 70)
        print()
        
        # Display user query if provided
        if user_query:
            print(f"❓ YOUR QUESTION: \"{user_query}\"")
            print()
        
        # Display snapshot
        snapshot = result.get("snapshot", {})
        if snapshot:
            income = snapshot.get("income", {})
            spending = snapshot.get("spending", {})
            savings = snapshot.get("savings", {})
            debt = snapshot.get("debt", {})
            profile = snapshot.get("profile", {})
            
            print("💰 FINANCIAL SNAPSHOT:")
            print(f"   Name: {profile.get('name', 'N/A')}")
            print(f"   Persona: {profile.get('persona', 'N/A')}")
            print(f"   Avg Monthly Income: ₹{income.get('average_monthly', 0):,.0f}")
            print(f"   Monthly Expenses: ₹{spending.get('total_monthly', 0):,.0f}")
            print(f"   Savings Balance: ₹{savings.get('current_balance', 0):,.0f}")
            print(f"   Emergency Fund: {savings.get('emergency_fund_months', 0):.1f} months")
            print(f"   Debt Outstanding: ₹{debt.get('total_outstanding', 0):,.0f}")
            print(f"   Financial Health Score: {snapshot.get('financial_health_score', 'N/A')}/100")
            print()
        
        # Display risk analysis
        risk_analysis = result.get("risk_analysis", {})
        if risk_analysis and risk_analysis.get("triggered_rules"):
            print("⚠️  RISK ANALYSIS:")
            for rule in risk_analysis["triggered_rules"]:
                severity = rule.get("severity", "medium").upper()
                rule_name = rule.get("rule_name", "Unknown")
                message = rule.get("message", "No details")
                print(f"   [{severity}] {rule_name}: {message}")
            print()
        
        # Display behavior
        behavior = result.get("behavior", {})
        if behavior:
            print("🎯 BEHAVIOR ANALYSIS:")
            print(f"   Risk Level: {behavior.get('risk_level', 'N/A')}")
            print(f"   Spending Pattern: {behavior.get('spending_pattern', 'N/A')}")
            if behavior.get("insights"):
                print(f"   Insights: {behavior['insights'][:200]}...")
            print()
        
        # Display advice
        advice = result.get("advice", {})
        if advice:
            print("💡 PERSONALIZED ADVICE:")
            
            # Display summary
            if advice.get("summary"):
                print(f"\n   📝 Summary: {advice['summary']}\n")
            
            # Display top risks
            if advice.get("top_risks"):
                print("   ⚠️  Top Risks:")
                for risk in advice["top_risks"]:
                    print(f"      • {risk}")
                print()
            
            # Display action steps
            if advice.get("action_steps"):
                print("   📋 Action Steps:")
                for i, step in enumerate(advice["action_steps"], 1):
                    title = step.get("title", "")
                    description = step.get("description", "")
                    priority = step.get("priority", "").upper()
                    print(f"      {i}. [{priority}] {title}")
                    print(f"         {description}")
                print()
            
            # Display tips
            if advice.get("savings_tip"):
                print(f"   💰 Savings Tip: {advice['savings_tip']}")
            if advice.get("spending_tip"):
                print(f"   🛍️  Spending Tip: {advice['spending_tip']}")
            if advice.get("stability_tip"):
                print(f"   📊 Stability Tip: {advice['stability_tip']}")
            
            if any([advice.get("savings_tip"), advice.get("spending_tip"), advice.get("stability_tip")]):
                print()
        
        # Display errors
        if result.get("errors"):
            print("⚠️  WARNINGS/ERRORS:")
            for error in result["errors"]:
                print(f"   • {error}")
            print()
        
        print("=" * 70)
        print("✅ Session completed successfully!")
        print("=" * 70)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user.")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """
    Run the main async function.
    
    Usage:
        python -m app.main
    
    Or:
        python app/main.py
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
