@echo off
REM Quick start script for Financial Coaching Agent

echo ========================================
echo Financial Coaching Agent - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your API keys!
    echo.
    pause
)

REM Run the application
echo Starting Financial Coaching Agent...
echo.
python -m app.main

pause
