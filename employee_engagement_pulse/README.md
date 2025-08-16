# Employee Engagement Pulse

A Slack sentiment analysis dashboard that transforms workplace chatter into actionable insights using **AI-powered sentiment analysis**.

## 🚀 New: AI-Enhanced Sentiment Analysis

Now powered by modern AI/LLMs for superior workplace understanding:
- **Context-aware analysis** - Understands sarcasm, technical jargon, team dynamics
- **Multiple AI providers** - OpenAI GPT, Anthropic Claude, or free Hugging Face models  
- **Burnout detection** - Identifies subtle stress signals and workload issues
- **Explainable results** - AI provides reasoning for each sentiment score

[📖 **AI Setup Guide**](docs/AI_SENTIMENT_GUIDE.md)

## Features

- 🤖 **AI-powered sentiment analysis** (NEW!)
- 📊 Real-time sentiment analysis of Slack messages
- 📈 Daily and weekly mood trends
- ⚠️ Advanced burnout detection and alerts
- 🎯 Channel-specific monitoring
- 📱 Interactive web dashboard
- 🧠 Explainable AI insights

## Quick Start

1. **Set up Python environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Enable AI sentiment analysis (recommended)**
```bash
setup_ai.bat  # Windows
# Follow prompts to install AI packages and configure providers
```

3. **Configure environment**
```bash
copy .env.example .env
# Edit .env with your Slack credentials
# Edit .env.ai with your AI provider settings
```

4. **Run the application**
```bash
uvicorn app.main:app --reload
```

4. **Start the frontend**
```bash
cd frontend
npm install
npm run dev
```

## Seeding with Fake Data

Generate synthetic Slack conversations for testing:

```bash
python app/seeds/seed_fake_slack.py --channels general random --days 14 --messages 200
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy + Slack Bolt
- **Frontend**: React + Chart.js
- **Database**: PostgreSQL
- **Deployment**: Docker + Docker Compose

## API Endpoints

- `/slack/` - Slack events webhook
- `/api/insights` - Get actionable insights
- `/api/channels` - Channel management
- `/api/sentiment/{channel}` - Channel sentiment data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
