# Quick start script for Financial Coaching Agent (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Financial Coaching Agent - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host ""
    Write-Host "IMPORTANT: Please edit .env file with your API keys!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to continue"
}

# Run the application
Write-Host "Starting Financial Coaching Agent..." -ForegroundColor Green
Write-Host ""
python -m app.main
