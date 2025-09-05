@echo off
echo ========================================
echo RAG System Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/upgrade requirements
echo.
echo Checking dependencies...
pip install -r requirements.txt -q

REM Start server and Qt app
echo.
echo ========================================
echo Starting RAG System...
echo ========================================
echo.

REM Start server in a new window
echo Starting server...
start "RAG Server" cmd /k "venv\Scripts\activate && python start_server.py"

REM Wait for server to start
echo Waiting for server to initialize...
timeout /t 5 /nobreak >nul

REM Start Qt application
echo Starting Qt interface...
start "RAG Qt App" cmd /k "venv\Scripts\activate && python qt_app_final.py"

echo.
echo ========================================
echo RAG System started successfully!
echo ========================================
echo.
echo Server running at: http://localhost:8000
echo.
echo To stop the system, close both windows.
echo.
pause
