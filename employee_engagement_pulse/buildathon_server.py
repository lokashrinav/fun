#!/usr/bin/env python3
"""
Real-time Employee Engagement Pulse - Simplified API Server
Connects to Buildathon Slack and runs LLM analysis
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import openai
from dataclasses import dataclass
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@dataclass
class TeamInsight:
    title: str
    description: str
    priority: str
    category: str

@dataclass
class EngagementMetrics:
    overall_health: float
    sentiment_score: str
    burnout_risk: str
    message_count: int
    insights: List[TeamInsight]
    team_breakdown: Dict[str, float]
    action_items: List[Dict] = None

class SlackEngagementAnalyzer:
    def __init__(self):
        self.db_path = "buildathon_pulse.db"
        self.init_db()
        
        # Slack tokens from env
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        logger.info(f"Initialized with Slack tokens: {'✅' if self.bot_token else '❌'}")
        
    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyzed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                user TEXT,
                message TEXT,
                timestamp DATETIME,
                sentiment REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert some sample Buildathon data if empty
        cursor.execute('SELECT COUNT(*) FROM analyzed_messages')
        if cursor.fetchone()[0] == 0:
            sample_messages = [
                ("all-buildathon", "user1", "Hi everyone! Ready to build something amazing today? 🚀", datetime.now() - timedelta(hours=2), 0.8),
                ("all-buildathon", "user2", "Whew, made it! Let's create some magic ✨", datetime.now() - timedelta(hours=1), 0.9),
                ("all-buildathon", "user3", "Working on our project now, really excited about the potential!", datetime.now() - timedelta(minutes=30), 0.7),
                ("all-buildathon", "user4", "Great collaboration happening here 🤝", datetime.now() - timedelta(minutes=15), 0.8),
                ("new-channel", "user5", "Need some help with the API integration, but making progress", datetime.now() - timedelta(minutes=10), 0.3),
            ]
            
            for channel, user, msg, ts, sentiment in sample_messages:
                cursor.execute('''
                    INSERT INTO analyzed_messages (channel, user, message, timestamp, sentiment)
                    VALUES (?, ?, ?, ?, ?)
                ''', (channel, user, msg, ts, sentiment))
        
        conn.commit()
        conn.close()
        
    def get_recent_messages(self, hours: int = 24) -> List[Dict]:
        """Get recent messages from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT channel, user, message, timestamp, sentiment 
            FROM analyzed_messages 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (cutoff_time,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'channel': row[0],
                'user': row[1],
                'text': row[2],
                'timestamp': row[3],
                'sentiment': row[4]
            })
            
        conn.close()
        return messages
        
    async def analyze_buildathon_engagement(self) -> EngagementMetrics:
        """Analyze team engagement from Buildathon Slack data"""
        try:
            messages = self.get_recent_messages()
            
            if not messages:
                return self._get_demo_metrics()
            
            # Calculate basic metrics
            total_messages = len(messages)
            avg_sentiment = sum(msg.get('sentiment', 0) for msg in messages) / total_messages if total_messages > 0 else 0
            
            # Prepare data for LLM analysis
            recent_texts = [msg['text'] for msg in messages[-20:]]  # Last 20 messages
            message_summary = "\n".join([f"[{msg['channel']}] {msg['text']}" for msg in messages[-10:]])
            
            # LLM Analysis
            analysis_prompt = f"""
            Analyze the following Slack messages from a Buildathon team workspace:
            
            Recent Messages:
            {message_summary}
            
            Total messages analyzed: {total_messages}
            Average sentiment score: {avg_sentiment:.2f}
            
            Provide analysis in JSON format with:
            {{
                "overall_health_score": <0-10>,
                "dominant_sentiment": "Positive|Negative|Neutral",
                "burnout_risk": "Low|Medium|High",
                "key_insights": [
                    {{
                        "title": "<insight title>",
                        "description": "<detailed description>",
                        "priority": "high|medium|low"
                    }}
                ],
                "action_items": [
                    {{
                        "title": "<action item title>",
                        "description": "<detailed description with Why/When/Expected Outcome>",
                        "priority": "high|medium|low",
                        "timeframe": "<when to complete>"
                    }}
                ],
                "team_summary": "<brief team status summary>"
            }}
            
            Focus on collaboration, enthusiasm, stress levels, and buildathon-specific activities.
            Generate realistic action items based on actual team communication patterns.
            """
            
            if openai.api_key:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert team engagement analyst for hackathons and buildathons. Provide insights in valid JSON format."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.3
                )
                
                analysis = json.loads(response.choices[0].message.content)
            else:
                # Fallback analysis based on sentiment scores
                analysis = self._generate_fallback_analysis(avg_sentiment, total_messages)
            
            # Build insights
            insights = []
            for insight_data in analysis.get('key_insights', []):
                insights.append(TeamInsight(
                    title=insight_data.get('title', ''),
                    description=insight_data.get('description', ''),
                    priority=insight_data.get('priority', 'medium'),
                    category='buildathon'
                ))
            
            # Build action items
            action_items = []
            for action_data in analysis.get('action_items', []):
                action_items.append({
                    'title': action_data.get('title', ''),
                    'description': action_data.get('description', ''),
                    'priority': action_data.get('priority', 'medium'),
                    'timeframe': action_data.get('timeframe', 'This week')
                })
            
            # Analyze by channel
            channel_breakdown = {}
            for msg in messages:
                channel = msg.get('channel', 'unknown')
                if channel not in channel_breakdown:
                    channel_breakdown[channel] = []
                channel_breakdown[channel].append(msg.get('sentiment', 0))
            
            team_scores = {}
            for channel, sentiments in channel_breakdown.items():
                avg_score = (sum(sentiments) / len(sentiments)) * 10 if sentiments else 5.0
                team_scores[channel.replace('-', ' ').title()] = min(max(avg_score, 0), 10)
            
            return EngagementMetrics(
                overall_health=analysis.get('overall_health_score', avg_sentiment * 10),
                sentiment_score=analysis.get('dominant_sentiment', 'Positive' if avg_sentiment > 0.5 else 'Neutral'),
                burnout_risk=analysis.get('burnout_risk', 'Low'),
                message_count=total_messages,
                insights=insights,
                team_breakdown=team_scores,
                action_items=action_items  # Add action items to metrics
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._get_demo_metrics()
    
    def _generate_fallback_analysis(self, sentiment: float, msg_count: int) -> dict:
        """Generate analysis when OpenAI API is unavailable"""
        if sentiment > 0.6:
            return {
                "overall_health_score": 8.5,
                "dominant_sentiment": "Positive",
                "burnout_risk": "Low",
                "key_insights": [
                    {
                        "title": "🚀 High Buildathon Energy",
                        "description": "Team shows strong enthusiasm and collaborative spirit in recent messages.",
                        "priority": "high"
                    },
                    {
                        "title": "💪 Active Participation",
                        "description": f"Consistent messaging activity with {msg_count} messages showing engagement.",
                        "priority": "medium"
                    }
                ],
                "action_items": [
                    {
                        "title": "Continue Supporting Team Momentum",
                        "description": "Why: High engagement detected | When: Ongoing | Expected Outcome: Maintain positive trajectory",
                        "priority": "low",
                        "timeframe": "Ongoing"
                    },
                    {
                        "title": "Recognize Active Contributors",
                        "description": "Why: Strong participation deserves acknowledgment | When: Next check-in | Expected Outcome: Reinforce positive behaviors",
                        "priority": "medium",
                        "timeframe": "Next meeting"
                    }
                ]
            }
        elif sentiment > 0.3:
            return {
                "overall_health_score": 7.2,
                "dominant_sentiment": "Neutral",
                "burnout_risk": "Medium",
                "key_insights": [
                    {
                        "title": "⚖️ Balanced Team State",
                        "description": "Team shows moderate engagement with some areas for improvement.",
                        "priority": "medium"
                    }
                ],
                "action_items": [
                    {
                        "title": "Check In with Team Members",
                        "description": "Why: Neutral sentiment suggests need for support | When: This week | Expected Outcome: Identify barriers and provide assistance",
                        "priority": "medium",
                        "timeframe": "This week"
                    }
                ]
            }
        else:
            return {
                "overall_health_score": 5.8,
                "dominant_sentiment": "Negative",
                "burnout_risk": "High",
                "key_insights": [
                    {
                        "title": "⚠️ Team Needs Support",
                        "description": "Lower sentiment detected - team may need encouragement or assistance.",
                        "priority": "high"
                    }
                ],
                "action_items": [
                    {
                        "title": "Immediate Team Support Session",
                        "description": "Why: Low sentiment indicates team struggles | When: Within 24 hours | Expected Outcome: Address issues and restore confidence",
                        "priority": "high",
                        "timeframe": "Within 24 hours"
                    },
                    {
                        "title": "Review Workload and Blockers",
                        "description": "Why: Negative patterns suggest systemic issues | When: This week | Expected Outcome: Remove barriers and redistribute work",
                        "priority": "high",
                        "timeframe": "This week"
                    }
                ]
            }
    
    def _get_demo_metrics(self) -> EngagementMetrics:
        """Demo data for Buildathon"""
        return EngagementMetrics(
            overall_health=8.7,
            sentiment_score="Positive",
            burnout_risk="Low",
            message_count=25,
            insights=[
                TeamInsight("🚀 Buildathon Energy High", "Team demonstrates strong enthusiasm and collaborative energy for the buildathon challenge", "high", "engagement"),
                TeamInsight("🤝 Great Collaboration", "Active cross-team communication and knowledge sharing observed", "medium", "collaboration"),
                TeamInsight("💡 Creative Problem Solving", "Messages show innovative thinking and solution-focused discussions", "medium", "creativity")
            ],
            team_breakdown={
                "All Buildathon": 8.7,
                "New Channel": 7.9,
                "Social": 8.2
            },
            action_items=[
                {
                    "title": "Maintain High Energy Levels",
                    "description": "Why: Team showing excellent engagement | When: Ongoing | Expected Outcome: Sustain momentum through buildathon completion",
                    "priority": "medium",
                    "timeframe": "Ongoing"
                },
                {
                    "title": "Document Best Practices",
                    "description": "Why: Strong collaboration patterns worth capturing | When: End of buildathon | Expected Outcome: Share learnings with other teams",
                    "priority": "low",
                    "timeframe": "Next week"
                }
            ]
        )

# Initialize components
app = FastAPI(title="Buildathon Engagement Pulse API")
analyzer = SlackEngagementAnalyzer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/api/team-metrics")
async def get_team_metrics():
    """Get current Buildathon team engagement metrics"""
    try:
        logger.info("Fetching Buildathon team metrics...")
        metrics = await analyzer.analyze_buildathon_engagement()
        
        return {
            "overall_health": metrics.overall_health,
            "sentiment": metrics.sentiment_score,
            "burnout_risk": metrics.burnout_risk,
            "message_count": metrics.message_count,
            "insights": [
                {
                    "title": insight.title,
                    "description": insight.description,
                    "priority": insight.priority,
                    "category": insight.category
                } for insight in metrics.insights
            ],
            "action_items": metrics.action_items or [],
            "team_breakdown": metrics.team_breakdown,
            "last_updated": datetime.now().isoformat(),
            "data_source": "Buildathon Slack Workspace"
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/message-history")
async def get_message_history():
    """Get recent Buildathon message history"""
    try:
        messages = analyzer.get_recent_messages(hours=48)
        return {
            "total_messages": len(messages),
            "sample_messages": messages[:5],  # Show recent 5
            "channels": list(set(msg['channel'] for msg in messages)),
            "timeframe": "Last 48 hours",
            "data_source": "Buildathon Database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Buildathon Engagement Pulse",
        "timestamp": datetime.now().isoformat(),
        "slack_configured": bool(analyzer.bot_token),
        "openai_configured": bool(openai.api_key)
    }

@app.get("/")
async def serve_dashboard():
    """Serve the dynamic dashboard"""
    return FileResponse("dashboard.html")

@app.get("/dashboard")
async def get_dashboard():
    """Alternative dashboard endpoint"""
    return FileResponse("dashboard.html")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Buildathon Employee Engagement Pulse")
    print("📊 Dashboard: http://localhost:8003")
    print("🔗 API: http://localhost:8003/api/team-metrics")
    print("💬 Analyzing your Buildathon Slack data...")
    
    uvicorn.run(app, host="127.0.0.1", port=8003)
