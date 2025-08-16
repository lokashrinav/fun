# Employee Engagement Pulse - Buildathon Project

A real-time Slack sentiment analysis and team engagement monitoring dashboard built with FastAPI and AI-powered insights.

## 🚀 Features

- **Real-time Slack Integration** - Monitors team communication patterns
- **AI-Powered Sentiment Analysis** - Uses OpenAI API for advanced sentiment detection
- **Burnout Risk Detection** - Identifies early warning signs of team burnout
- **Interactive Dashboard** - Beautiful web interface with live metrics
- **Team Health Scoring** - Quantifies team engagement and wellness
- **Actionable Insights** - AI-generated recommendations for managers

## 📊 Dashboard Metrics

- Overall Team Health Score (0-10)
- Sentiment Analysis (Positive/Neutral/Negative)
- Burnout Risk Assessment (Low/Medium/High)
- Communication Volume Tracking
- Channel-specific Analysis
- Weekly Trend Analysis

## 🛠 Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: SQLite with SQLAlchemy ORM
- **AI/ML**: OpenAI GPT API, NLTK VADER
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Integration**: Slack Bolt SDK
- **Scheduling**: APScheduler for background jobs

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API Key
- Slack App credentials (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/PrasannPradeepPatil/Buildathon-Project3.git
cd Buildathon-Project3
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the application:
```bash
cd employee_engagement_pulse
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Access the dashboard:
- API: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard

## 📁 Project Structure

```
employee_engagement_pulse/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api.py               # API routes and endpoints
│   ├── models.py            # SQLAlchemy database models
│   ├── sentiment.py         # Sentiment analysis engine
│   ├── aggregator.py        # Data aggregation and summary generation
│   ├── insights.py          # AI insights generation
│   ├── scheduler.py         # Background job scheduling
│   └── slack_events.py      # Slack integration handlers
├── dashboard.html           # Main dashboard interface
├── test_dashboard.html      # Testing dashboard
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

### Environment Variables (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your_slack_signing_secret
DATABASE_URL=sqlite:///./employee_pulse.db
LOG_LEVEL=INFO
```

## 📈 API Endpoints

- `GET /api/channels` - List all monitored channels
- `GET /api/team-metrics` - Get team health metrics
- `GET /api/sentiment/{channel_id}` - Channel-specific sentiment
- `GET /api/insights` - AI-generated insights
- `GET /api/dashboard` - Comprehensive dashboard data
- `POST /slack/events` - Slack webhook endpoint

## 🤖 AI Features

- **Sentiment Analysis**: NLTK VADER + custom work-specific keywords
- **Emoji Processing**: Unicode and Slack emoji sentiment scoring
- **Burnout Detection**: Multi-factor risk assessment
- **Insight Generation**: AI-powered team recommendations
- **Trend Analysis**: Weekly engagement pattern detection

## 🚀 Deployment

The application is ready for deployment on platforms like:
- Heroku
- Railway
- DigitalOcean App Platform
- AWS Elastic Beanstalk
- Google Cloud Run

## 🏆 Buildathon Achievement

This project demonstrates:
- ✅ Full-stack development with modern Python frameworks
- ✅ AI/ML integration for practical business use cases
- ✅ Real-time data processing and visualization
- ✅ Clean, maintainable code architecture
- ✅ Production-ready deployment configuration

## 👥 Team

Built for the Buildathon competition - showcasing rapid development of AI-powered workplace analytics.

## 📄 License

MIT License - See LICENSE file for details.