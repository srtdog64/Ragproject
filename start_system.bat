@echo off
REM ========================================
REM RAG System Launcher for Windows
REM ========================================

echo ========================================
echo     RAG System Launcher
echo ========================================
echo.

REM Navigate to script directory
cd /d %~dp0

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check dependencies (silent)
echo Checking dependencies...
pip install -q -r requirements.txt 2>nul

REM Run the cross-platform main script
echo.
echo Starting RAG System...
python main.py %*

pause
