@echo off
echo 🚀 Starting Employee Engagement Pulse Server
echo ============================================

echo Changing to project directory...
cd /d C:\Users\lokas\build1\employee_engagement_pulse

echo Starting FastAPI server...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
