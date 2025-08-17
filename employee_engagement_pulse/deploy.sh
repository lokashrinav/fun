#!/bin/bash

# Employee Engagement Pulse Deployment Script
echo "🚀 Deploying Employee Engagement Pulse..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Login to Heroku (if not already logged in)
echo "🔐 Checking Heroku login..."
heroku auth:whoami || heroku login

# Create Heroku app
APP_NAME="employee-engagement-pulse-$(date +%s)"
echo "🏗️  Creating Heroku app: $APP_NAME"
heroku create $APP_NAME

# Set environment variables
echo "⚙️  Setting environment variables..."
echo "Please enter your Slack Bot Token:"
read -s SLACK_BOT_TOKEN
heroku config:set SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN --app $APP_NAME

# Deploy to Heroku
echo "📦 Deploying to Heroku..."
git add .
git commit -m "Deploy Employee Engagement Pulse"
git push heroku main

# Open the app
echo "✅ Deployment complete!"
echo "🌐 Opening your app..."
heroku open --app $APP_NAME

echo "📊 Your Employee Engagement Pulse is now live!"
echo "🔗 App URL: https://$APP_NAME.herokuapp.com"
