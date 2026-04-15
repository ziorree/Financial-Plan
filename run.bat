@echo off
REM Setup and run script for Financial Planner App on Windows

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed. Please install Python 3.8 or later.
    exit /b 1
)

REM Create virtual environment (optional but recommended)
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install requirements
echo Installing dependencies...
python -m pip install -q -r requirements.txt

REM Run the Streamlit app
echo.
echo Starting Financial Planner App...
echo The app will open at http://localhost:8501
echo.

streamlit run app.py

pause
