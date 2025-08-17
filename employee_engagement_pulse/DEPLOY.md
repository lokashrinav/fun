# Employee Engagement Pulse - Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Heroku (Recommended)
```bash
# Install Heroku CLI first: https://devcenter.heroku.com/articles/heroku-cli
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Railway
```bash
# Install Railway CLI: npm install -g @railway/cli
railway login
railway init
railway add
railway deploy
```

### Option 3: Render
1. Connect your GitHub repo to Render
2. Set environment variable: `SLACK_BOT_TOKEN=your_bot_token`
3. Build command: `pip install -r requirements.txt`
4. Start command: `python working_server.py`

### Option 4: Local Development
```bash
python working_server.py
# Access at http://localhost:8008
```

## 🔧 Environment Variables Needed
- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...)
- `PORT`: Server port (automatically set by most platforms)

## 📋 Features Deployed
✅ Real Slack integration  
✅ Team sentiment analysis  
✅ Weekly trend tracking  
✅ Burnout detection  
✅ Interactive dashboard  
✅ Real-time metrics  

## 🔗 API Endpoints
- `/` - Main dashboard
- `/api/channels` - List Slack channels  
- `/api/team-metrics` - Team engagement metrics

## 📊 Live Demo
Your Employee Engagement Pulse dashboard provides:
- Real-time team sentiment analysis
- Weekly mood trends and burnout warnings  
- Actionable insights for managers
- Direct integration with your Slack workspace
