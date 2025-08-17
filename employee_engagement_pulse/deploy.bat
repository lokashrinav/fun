@echo off
echo 🚀 Employee Engagement Pulse - Windows Deploy
echo.

REM Check if Heroku CLI is installed
where heroku >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Heroku CLI not found. Please install it first:
    echo    https://devcenter.heroku.com/articles/heroku-cli
    pause
    exit /b 1
)

REM Check Heroku login
echo 🔐 Checking Heroku login...
heroku auth:whoami >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Please login to Heroku...
    heroku login
)

REM Create unique app name
for /f %%i in ('powershell -command "Get-Date -UFormat %%s"') do set TIMESTAMP=%%i
set APP_NAME=employee-engagement-pulse-%TIMESTAMP:~0,8%

echo 🏗️  Creating Heroku app: %APP_NAME%
heroku create %APP_NAME%

REM Set environment variables
echo.
echo ⚙️  Setting up environment variables...
set /p SLACK_BOT_TOKEN="Please enter your Slack Bot Token: "
heroku config:set SLACK_BOT_TOKEN=%SLACK_BOT_TOKEN% --app %APP_NAME%

REM Deploy
echo.
echo 📦 Deploying to Heroku...
git add .
git commit -m "Deploy Employee Engagement Pulse"
git push heroku main

REM Open app
echo.
echo ✅ Deployment complete!
echo 🌐 Opening your app...
heroku open --app %APP_NAME%

echo.
echo 📊 Your Employee Engagement Pulse is now live!
echo 🔗 App URL: https://%APP_NAME%.herokuapp.com
pause
