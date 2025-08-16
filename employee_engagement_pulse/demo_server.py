#!/usr/bin/env python3
"""
Demo Employee Engagement Pulse API - Minimal working version
Shows AI sentiment analysis and database integration without Slack dependencies
"""
import os
import json
from datetime import datetime, date
from typing import Dict, List, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Load environment variables
project_dir = Path(__file__).parent
env_file = project_dir / ".env"
load_dotenv(dotenv_path=env_file)

# Initialize FastAPI
app = FastAPI(
    title="Employee Engagement Pulse - Demo",
    description="AI-powered sentiment analysis for workplace communication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import our AI sentiment analyzer
import sys
sys.path.append(str(Path(__file__).parent))

@app.get("/", response_class=HTMLResponse)
async def root():
    """Welcome page with system status"""
    
    # Check AI status
    openai_key = os.getenv("OPENAI_API_KEY")
    ai_status = "✅ Active" if openai_key and openai_key.startswith("sk-") else "⚠️ Demo Mode"
    
    # Check Slack status
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_secret = os.getenv("SLACK_SIGNING_SECRET") 
    
    if slack_token and slack_secret:
        slack_status = "✅ Fully Connected"
    elif slack_token:
        slack_status = "⚠️ Token Only (Missing Signing Secret)"
    elif slack_secret:
        slack_status = "⚠️ Secret Only (Missing Bot Token)"
    else:
        slack_status = "❌ Not Configured"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Employee Engagement Pulse</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .status {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .demo-section {{ background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            button {{ background: #007cba; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #005a87; }}
            .result {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Employee Engagement Pulse</h1>
            <p>AI-powered sentiment analysis for workplace communication</p>
            
            <div class="status">
                <h3>📊 System Status</h3>
                <p><strong>AI Sentiment Analysis:</strong> {ai_status}</p>
                <p><strong>Slack Integration:</strong> {slack_status}</p>
                <p><strong>Database:</strong> ✅ SQLite Ready</p>
                <p><strong>API Server:</strong> ✅ Running on Port 8000</p>
            </div>
            
            <div class="demo-section">
                <h3>🧪 Try AI Sentiment Analysis</h3>
                <p>Test workplace messages to see how the AI understands sentiment:</p>
                
                <div id="demo-messages">
                    <button onclick="analyzeMessage('This deployment is taking forever and I\\'m frustrated 😤')">
                        🔴 Test: Frustrated Developer
                    </button>
                    <button onclick="analyzeMessage('Great job everyone on the release! 🎉 Zero bugs so far')">
                        🟢 Test: Team Celebration
                    </button>
                    <button onclick="analyzeMessage('Oh great, another bug right before the weekend...')">
                        🟡 Test: Sarcasm Detection
                    </button>
                    <button onclick="analyzeMessage('Sure, I can take on another project. Why not...')">
                        🟠 Test: Workload Stress
                    </button>
                </div>
                
                <div id="result" style="display: none;"></div>
            </div>
            
            <div class="demo-section">
                <h3>📈 Available Endpoints</h3>
                <ul>
                    <li><a href="/analyze" target="_blank">POST /analyze</a> - Analyze sentiment of text</li>
                    <li><a href="/dashboard" target="_blank">GET /dashboard</a> - View sentiment dashboard</li>
                    <li><a href="/docs" target="_blank">GET /docs</a> - Interactive API Documentation</li>
                </ul>
            </div>
            
            <div class="demo-section">
                <h3>🔗 Next Steps</h3>
                <p>To enable full functionality:</p>
                <ol>
                    <li><strong>Slack Integration:</strong> Add your Slack Bot Token and Signing Secret</li>
                    <li><strong>Frontend Dashboard:</strong> Start the React frontend with <code>npm run dev</code></li>
                    <li><strong>Real-time Monitoring:</strong> Configure Slack webhook URLs</li>
                </ol>
            </div>
        </div>
        
        <script>
        async function analyzeMessage(text) {{
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerHTML = '<p>🔄 Analyzing: "' + text + '"...</p>';
            
            try {{
                const response = await fetch('/analyze', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ text: text }})
                }});
                
                const result = await response.json();
                
                let sentimentEmoji = result.score >= 0.3 ? '😊' : result.score <= -0.3 ? '😞' : '😐';
                let sentimentText = result.score >= 0.3 ? 'Positive' : result.score <= -0.3 ? 'Negative' : 'Neutral';
                
                document.getElementById('result').innerHTML = `
                    <div class="result">
                        <p><strong>📝 Message:</strong> "${{text}}"</p>
                        <p><strong>📊 Sentiment:</strong> ${{sentimentEmoji}} ${{result.score.toFixed(2)}} (${{sentimentText}})</p>
                        <p><strong>🎯 Confidence:</strong> ${{(result.confidence * 100).toFixed(0)}}%</p>
                        <p><strong>🧠 AI Reasoning:</strong> ${{result.reasoning}}</p>
                    </div>
                `;
            }} catch (error) {{
                document.getElementById('result').innerHTML = '<p>❌ Error: ' + error.message + '</p>';
            }}
        }}
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
async def analyze_sentiment(request: Dict[str, str]):
    """Analyze sentiment of provided text using AI"""
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Use our AI sentiment analyzer
        from app.enhanced_sentiment_simple import ai_sentiment_analyzer
        
        result = ai_sentiment_analyzer.analyze_message_sentiment(text)
        
        return {
            "text": text,
            "score": result["score"],
            "confidence": result["confidence"], 
            "reasoning": result["reasoning"],
            "timestamp": datetime.now().isoformat(),
            "ai_provider": ai_sentiment_analyzer.provider
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/dashboard")
async def get_dashboard():
    """Get dashboard data"""
    try:
        from app.models import SessionLocal, Sentiment
        
        db = SessionLocal()
        sentiments = db.query(Sentiment).limit(50).all()
        db.close()
        
        dashboard_data = []
        for sentiment in sentiments:
            dashboard_data.append({
                "id": sentiment.id,
                "text": sentiment.text_content,
                "score": sentiment.sentiment_score,
                "confidence": sentiment.confidence,
                "timestamp": sentiment.created_at.isoformat(),
                "channel": sentiment.channel_id,
                "user": sentiment.user_id
            })
        
        avg_sentiment = sum(s["score"] for s in dashboard_data) / len(dashboard_data) if dashboard_data else 0
        
        return {
            "summary": {
                "total_messages": len(dashboard_data),
                "average_sentiment": round(avg_sentiment, 3),
                "last_updated": datetime.now().isoformat()
            },
            "recent_sentiments": dashboard_data
        }
        
    except Exception as e:
        return {
            "summary": {
                "total_messages": 0,
                "average_sentiment": 0,
                "last_updated": datetime.now().isoformat(),
                "note": "Database not initialized - run some analysis first"
            },
            "recent_sentiments": []
        }

@app.get("/debug")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "working_directory": str(Path.cwd()),
        "script_directory": str(Path(__file__).parent),
        "env_file_exists": (Path(__file__).parent / ".env").exists(),
        "slack_token_present": bool(os.getenv("SLACK_BOT_TOKEN")),
        "slack_token_prefix": os.getenv("SLACK_BOT_TOKEN", "")[:10] + "..." if os.getenv("SLACK_BOT_TOKEN") else "None",
        "signing_secret_present": bool(os.getenv("SLACK_SIGNING_SECRET")),
        "signing_secret_prefix": os.getenv("SLACK_SIGNING_SECRET", "")[:8] + "..." if os.getenv("SLACK_SIGNING_SECRET") else "None",
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "slack_configured": bool(os.getenv("SLACK_BOT_TOKEN"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
