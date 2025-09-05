@echo off
echo ========================================
echo Installing Gemini API Support
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Installing aiohttp for Gemini API...
pip install aiohttp

echo.
echo Installation complete!
echo.
echo Make sure .env file contains:
echo GEMINI_API_KEY=your_api_key
echo.
pause
