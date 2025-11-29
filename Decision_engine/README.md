# Decision Engine (FastAPI)

A lightweight financial Decision Engine that consumes an intelligence-rich JSON (see `sample.json`) and returns risks, rule triggers, recommendations with reasons, and an action plan. Exposes FastAPI endpoints.

## Quick Start

1) Create a virtual environment and install dependencies

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -U pip; pip install -r requirements.txt
```

2) Run the API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3) Try endpoints

- Health: `GET http://localhost:8000/health`
- Evaluate using repo sample: `GET http://localhost:8000/demo`
- Evaluate with POST body (send your JSON):

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/evaluate -ContentType 'application/json' -Body (Get-Content .\sample.json -Raw)
```

## Endpoints

- `GET /health` – health check
- `POST /evaluate` – evaluate an input JSON matching `sample.json` shape
- `GET /demo` – evaluates the bundled `sample.json`

## Implementation Notes

- FastAPI wiring: `app/main.py`
- Orchestrator: `engine/engine.py`
- Schemas: `engine/models.py`
- Normalization: `engine/normalization.py`
- Rules: `engine/rules.py`
- Risks: `engine/risks.py`
- Recommendations: `engine/recommendations.py`

## Local Smoke Test (no server)

```powershell
python .\scripts\run_sample.py | Out-File -FilePath out.json -Encoding UTF8; Get-Content .\out.json -TotalCount 60
```
