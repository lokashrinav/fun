@echo off
echo.
echo ======================================================
echo   Employee Engagement Pulse - Windows Setup
echo ======================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Run the setup script
echo Running setup script...
python setup.py %*

echo.
echo Setup script completed!
echo.
echo To start the application:
echo 1. Open a terminal and run: uvicorn app.main:app --reload
echo 2. Open another terminal, go to frontend folder, and run: npm start
echo 3. Open http://localhost:3000 in your browser
echo.

pause
