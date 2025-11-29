# Autonomous Financial Coaching Agent (FinMentor)

This project implements a **hybrid Rule-Based + Agentic AI system** for generating financial insights and advice for users with **irregular income** (gig workers, vendors, etc.).

---


![WhatsApp Image 2025-11-29 at 11 28 50_b86ed624](https://github.com/user-attachments/assets/dc6281e5-1598-4644-90e5-5adb717ced59)


## 1. What We Built

- A **custom rule-based decision engine** for financial risk detection
- An **Agentic AI layer** that reasons over rule outputs
- A system that generates:
  - Risk scores
  - Explainable recommendations
  - Action plans
  - Proactive alerts
- Designed for **irregular and volatile income patterns**

---

## 2. Core System Pipeline
User Financial Data <br>
↓<br>
Rule Engine Evaluation<br>
↓<br>
Risk & Trigger JSON Output<br>
↓<br>
Agentic Reasoning (LangGraph)<br>
↓<br>
Advice + Action Plan <br>

---

## 3. Rule Engine Design (What We Actually Implemented)

Rules are implemented as **deterministic financial conditions**.

Each rule contains:
- `rule_id`
- `severity`
- `weight`
- `params` (actual user values)
- `triggered` flag
- `data_refs` (source fields)

### Implemented Rule Categories:
- Savings Rate Rules
- Emergency Fund Rules
- Cashflow Stability Rules
- Discretionary Spending Rules
- Category Drift Rules

### Example Logic Used:
- If `savings_rate < 0.25` → High Risk
- If `buffer_months < 4` → High Risk
- If `discretionary_ratio > 0.25` → Overspending
- If category spend increases > 30% → Drift detected

### Output of Rule Engine:
- `risks[]` → Aggregated risk objects
- `rule_triggers[]` → All triggered rules with parameters
- `weighted_score` → Final risk score per dimension
- `recommendations[]` → Rule-linked suggestions
- `action_plan[]` → User tasks

All outputs are produced as **structured JSON**.

---

## 4. Why We Did Not Use Only LLMs for Decisions

- Financial decisions require **determinism and explainability**
- LLMs alone are:
  - Non-deterministic
  - Not regulation safe
  - Not numerically reliable

So we use:
- ✅ Rules for **financial correctness**
- ✅ Agent for **reasoning and personalization**

---

## 5. Agentic Reasoning (How the AI Works)

The agent does NOT calculate finances.  
It **reasons on top of rule engine output**.

### Inputs to the Agent:
- User financial snapshot
- Rule engine JSON output
- Historical user behavior (memory)

### The Agent Decides:
- Which risks are most important
- What advice to prioritize
- Whether an alert is needed
- What action plan to generate

---

## 6. Agent Tools (LangGraph Nodes)

We model the system as tools:

- `rule_engine_tool` → Fetches risk JSON
- `trend_analysis_tool` → Detects income & spend trends
- `recommendation_tool` → Generates advice
- `alert_tool` → Triggers urgent notifications
- `action_plan_tool` → Creates 30-day goals

Each tool is a **separate callable function** in the agent graph.

---

## 7. Proactive (Autonomous) Behavior

The system runs periodically and:
- Re-evaluates rules
- Compares with previous data
- Triggers alerts automatically when:
  - Income drops suddenly
  - Emergency fund hits 0
  - Spending spikes abnormally

This makes the system **autonomous, not reactive**.

---

## 8. Explainability Layer

Every recommendation includes:
- `linked_risks`
- `triggered_rule_id`
- Actual numerical parameters used
- Severity & confidence

This ensures **complete traceability from data → rule → advice**.

---

## 9. Tech Stack Used

- Backend: Python, .NET
- Rule Engine: Custom JSON-based evaluator
- Agent Framework: LangGraph (LangChain)
- LLM: OpenAI / Open-source LLM
- Database: MySQL
- API: FastAPI
- Frontend : React 

---

## 10. What Makes This Agentic

- Persistent memory across time
- Tool-based execution
- Autonomous background evaluation
- Dynamic goal generation
- Multi-step reasoning using rules + LLM

This is **not prompt-based chat**, it is **goal-driven agent execution**.

---
