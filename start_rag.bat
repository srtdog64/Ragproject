@echo off
echo ========================================
echo RAG System Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if requirements are installed
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing requirements...
    pip install -r requirements.txt
    echo.
)

REM Install PySide6 for Qt UI if not installed
pip show PySide6 >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PySide6 for Qt interface...
    pip install "PySide6>=6.8.0"
    echo.
)

echo Starting RAG Server and UI...
echo.

REM Start server in background
start "RAG Server" cmd /c "venv\Scripts\activate && python run_server.py"

REM Wait for server to start
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Start Qt UI
echo Starting Qt6 Interface...
python qt_app_final.py

pause
