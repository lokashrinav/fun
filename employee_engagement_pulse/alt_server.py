#!/usr/bin/env python3
"""
Alternative server approach using different uvicorn configuration
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from dotenv import load_dotenv
from simple_slack_analyzer import SimpleSlackAnalyzer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
try:
    slack_analyzer = SimpleSlackAnalyzer()
    logger.info("✅ Slack analyzer initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Slack analyzer: {e}")
    slack_analyzer = None

@app.get("/")
async def serve_dashboard():
    """Serve the dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/api/channels")
async def get_channels():
    """Get Slack channels - simplified version"""
    logger.info("🔍 Getting channels...")
    
    if slack_analyzer:
        try:
            channels = slack_analyzer.get_channels()
            channel_names = [ch['name'] for ch in channels]
            logger.info(f"✅ Found {len(channel_names)} channels: {channel_names}")
            
            return {
                "channels": channel_names,
                "total_count": len(channel_names),
                "data_source": "Real Slack API",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"❌ Error getting channels: {e}")
            return {
                "channels": ["buildathon-general", "team-updates", "random"],
                "total_count": 3,
                "data_source": "Fallback Data",
                "status": "fallback",
                "error": str(e)
            }
    else:
        return {
            "channels": ["buildathon-general", "team-updates", "random"],
            "total_count": 3,
            "data_source": "No Slack Connection",
            "status": "offline"
        }

@app.get("/api/team-metrics")
async def get_team_metrics():
    """Get team metrics - simplified version"""
    logger.info("📊 Getting team metrics...")
    
    if slack_analyzer:
        try:
            metrics = slack_analyzer.get_simple_metrics()
            logger.info(f"✅ Got metrics: health={metrics['overall_health']}")
            return metrics
        except Exception as e:
            logger.error(f"❌ Error getting metrics: {e}")
            return {
                "overall_health": 75.0,
                "sentiment": "Working on it",
                "burnout_risk": "Low",
                "message_count": 0,
                "insights": [f"Error: {str(e)}", "🔄 Debugging Slack integration"],
                "action_items": ["🛠️ Fixing connection issues"],
                "channels": ["error"],
                "real_data_stats": {"status": "error", "error": str(e)}
            }
    else:
        return {
            "overall_health": 60.0,
            "sentiment": "Offline",
            "burnout_risk": "Unknown",
            "message_count": 0,
            "insights": ["🔌 Slack analyzer not initialized"],
            "action_items": ["🛠️ Check Slack configuration"],
            "channels": ["offline"],
            "real_data_stats": {"status": "offline"}
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Employee Engagement Pulse - Alternative Server")
    print("📊 Dashboard: http://localhost:8008")
    
    # Use different uvicorn configuration
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8008,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
