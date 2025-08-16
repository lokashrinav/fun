#!/usr/bin/env python3
"""
Minimal test server to debug the crash
"""

from fastapi import FastAPI
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test server is working"}

@app.get("/api/test")
async def test():
    """Simple test endpoint"""
    try:
        logger.info("📋 Test endpoint called")
        return {
            "status": "working",
            "message": "Basic endpoint works"
        }
    except Exception as e:
        logger.error(f"❌ Error in test endpoint: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting TEST server")
    print("📊 Test URL: http://localhost:8006")
    uvicorn.run(app, host="127.0.0.1", port=8006)
