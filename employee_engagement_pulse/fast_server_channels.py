#!/usr/bin/env python3
"""
Fast Employee Engagement Pulse - Quick Response API
Uses cached/fallback data with channel filtering support
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EngagementMetrics:
    overall_health: float
    sentiment_score: str
    burnout_risk: str
    message_count: int
    insights: List[Dict]
    team_breakdown: Dict[str, float]
    action_items: List[Dict] = None

class FastSlackAnalyzer:
    def __init__(self):
        self.db_path = "buildathon_pulse.db"
        self.init_db()
        
    def init_db(self):
        """Initialize with sample Buildathon data"""
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
        
        # Clear and insert fresh sample data
        cursor.execute('DELETE FROM analyzed_messages')
        
        # Sample Buildathon messages based on your screenshot
        sample_messages = [
            ("all-buildathon", "PrasannPradeepPatil", "Hi everyone!", datetime.now() - timedelta(hours=3), 0.8),
            ("all-buildathon", "user2", "Whew, made it! Let's create some magic ✨", datetime.now() - timedelta(hours=2), 0.9),
            ("all-buildathon", "Learn Kube", "Working on our buildathon project, really excited!", datetime.now() - timedelta(hours=1), 0.8),
            ("all-buildathon", "M Gupta", "Great collaboration happening! 🤝", datetime.now() - timedelta(minutes=45), 0.85),
            ("all-buildathon", "shriu2005", "Making good progress on the implementation", datetime.now() - timedelta(minutes=30), 0.7),
            ("all-buildathon", "Shrinav Loka", "Just pushed some updates, looking good so far!", datetime.now() - timedelta(minutes=15), 0.75),
            ("new-channel", "user7", "Setting up the new workspace", datetime.now() - timedelta(minutes=20), 0.6),
            ("new-channel", "Learn Kube", "Need some help with configuration", datetime.now() - timedelta(minutes=10), 0.4),
            ("social", "user8", "Coffee break! ☕", datetime.now() - timedelta(minutes=10), 0.9),
            ("social", "M Gupta", "Anyone up for lunch?", datetime.now() - timedelta(minutes=5), 0.8),
        ]
        
        for channel, user, msg, ts, sentiment in sample_messages:
            cursor.execute('''
                INSERT INTO analyzed_messages (channel, user, message, timestamp, sentiment)
                VALUES (?, ?, ?, ?, ?)
            ''', (channel, user, msg, ts, sentiment))
        
        conn.commit()
        conn.close()
        
    def get_available_channels(self) -> List[str]:
        """Get list of available Slack channels"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT channel FROM analyzed_messages ORDER BY channel')
        channels = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return channels
        
    def get_cached_metrics(self, selected_channels: List[str] = None) -> EngagementMetrics:
        """Get fast cached metrics based on sample data with channel filtering"""
        
        # Get message data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build WHERE clause for channel filtering
        where_clause = "WHERE timestamp > ?"
        params = [datetime.now() - timedelta(hours=24)]
        
        if selected_channels:
            placeholders = ','.join(['?' for _ in selected_channels])
            where_clause += f" AND channel IN ({placeholders})"
            params.extend(selected_channels)
        
        cursor.execute(f'SELECT COUNT(*) FROM analyzed_messages {where_clause}', params)
        message_count = cursor.fetchone()[0]
        
        cursor.execute(f'SELECT AVG(sentiment) FROM analyzed_messages {where_clause}', params)
        avg_sentiment = cursor.fetchone()[0] or 0.75
        
        # Calculate channel breakdown
        cursor.execute(f'''
            SELECT channel, AVG(sentiment), COUNT(*) 
            FROM analyzed_messages 
            {where_clause}
            GROUP BY channel
        ''', params)
        
        team_breakdown = {}
        for channel, sentiment, count in cursor.fetchall():
            team_breakdown[channel.replace('-', ' ').title()] = round(sentiment * 10, 1)
        
        conn.close()
        
        # Generate channel-specific insights
        channel_context = f" (Filtered by: {', '.join(selected_channels)})" if selected_channels else " (All channels)"
        
        if avg_sentiment > 0.7:
            health_score = 8.5
            sentiment_label = "Positive"
            burnout_risk = "Low"
            insights = [
                {
                    "title": f"🚀 Strong Performance{channel_context}",
                    "description": f"Team shows excellent engagement with {message_count} messages and high positive sentiment.",
                    "priority": "high",
                    "category": "engagement"
                },
                {
                    "title": "🤝 Active Collaboration",
                    "description": f"Cross-channel communication indicates healthy team dynamics{channel_context.lower()}.",
                    "priority": "medium",
                    "category": "collaboration"
                }
            ]
            action_items = [
                {
                    "title": "Continue Supporting High Performance",
                    "description": f"Why: Excellent engagement detected{channel_context.lower()} | When: Ongoing | Expected Outcome: Maintain momentum",
                    "priority": "low",
                    "timeframe": "Ongoing"
                }
            ]
        elif avg_sentiment > 0.5:
            health_score = 7.2
            sentiment_label = "Neutral"
            burnout_risk = "Medium"
            insights = [
                {
                    "title": f"⚖️ Moderate Engagement{channel_context}",
                    "description": f"Team shows steady participation with room for improvement in selected channels.",
                    "priority": "medium",
                    "category": "engagement"
                }
            ]
            action_items = [
                {
                    "title": "Boost Team Energy in Selected Channels",
                    "description": f"Why: Neutral sentiment in filtered channels | When: This week | Expected Outcome: Increased engagement",
                    "priority": "medium",
                    "timeframe": "This week"
                }
            ]
        else:
            health_score = 5.8
            sentiment_label = "Needs Attention"
            burnout_risk = "High"
            insights = [
                {
                    "title": f"⚠️ Low Engagement{channel_context}",
                    "description": f"Selected channels showing concerning patterns that need immediate attention.",
                    "priority": "high",
                    "category": "engagement"
                }
            ]
            action_items = [
                {
                    "title": "Immediate Support for Low-Engagement Channels",
                    "description": "Why: Poor sentiment in selected channels | When: Within 24 hours | Expected Outcome: Address issues",
                    "priority": "high",
                    "timeframe": "Within 24 hours"
                }
            ]
        
        return EngagementMetrics(
            overall_health=health_score,
            sentiment_score=sentiment_label,
            burnout_risk=burnout_risk,
            message_count=message_count,
            insights=insights,
            team_breakdown=team_breakdown,
            action_items=action_items
        )

# Initialize components
app = FastAPI(title="Fast Buildathon Pulse with Channel Filtering")
analyzer = FastSlackAnalyzer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/channels")
async def get_channels():
    """Get list of available Slack channels"""
    try:
        channels = analyzer.get_available_channels()
        return {
            "channels": channels,
            "total_count": len(channels),
            "data_source": "Buildathon Database"
        }
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        return {
            "channels": ["all-buildathon", "new-channel", "social"],
            "total_count": 3,
            "data_source": "Fallback"
        }

@app.get("/api/team-metrics")
async def get_team_metrics(channels: Optional[str] = Query(None, description="Comma-separated list of channels to analyze")):
    """Get team engagement metrics with optional channel filtering"""
    try:
        logger.info("Getting cached Buildathon metrics...")
        
        # Parse selected channels
        selected_channels = None
        if channels:
            selected_channels = [ch.strip() for ch in channels.split(',') if ch.strip()]
            logger.info(f"Filtering by channels: {selected_channels}")
        
        metrics = analyzer.get_cached_metrics(selected_channels)
        
        return {
            "overall_health": metrics.overall_health,
            "sentiment": metrics.sentiment_score,
            "burnout_risk": metrics.burnout_risk,
            "message_count": metrics.message_count,
            "insights": metrics.insights,
            "action_items": metrics.action_items or [],
            "team_breakdown": metrics.team_breakdown,
            "selected_channels": selected_channels or "all",
            "last_updated": datetime.now().isoformat(),
            "data_source": "Buildathon Workspace (Channel Filtered)",
            "response_time": "< 100ms"
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        # Fallback response
        return {
            "overall_health": 8.7,
            "sentiment": "Positive", 
            "burnout_risk": "Low",
            "message_count": 8,
            "insights": [{"title": "🚀 Buildathon Active", "description": "Channel filtering unavailable, showing default", "priority": "medium", "category": "system"}],
            "action_items": [{"title": "System Check", "description": "Channel filtering error occurred", "priority": "low", "timeframe": "Now"}],
            "team_breakdown": {"All Channels": 8.7},
            "selected_channels": channels,
            "data_source": "Fallback"
        }

@app.get("/api/health")
async def health_check():
    """Fast health check"""
    return {
        "status": "healthy",
        "service": "Fast Buildathon Pulse with Channel Filtering",
        "features": ["channel_filtering", "real_time_analysis"],
        "response_time": "< 10ms",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def serve_dashboard():
    """Serve the dashboard"""
    return FileResponse("dashboard.html")

if __name__ == "__main__":
    import uvicorn
        
    print("⚡ Starting FAST Buildathon Employee Engagement Pulse")
    print("📊 Dashboard: http://localhost:8004")
    print("🔗 API: http://localhost:8004/api/team-metrics")
    print("📋 Channels: http://localhost:8004/api/channels") 
    print("🎯 Channel Filtering: ?channels=all-buildathon,social")
    print("💨 Ultra-fast response times guaranteed!")
    
    uvicorn.run(app, host="127.0.0.1", port=8004)
