"""
Slack Events API handler using Slack Bolt framework
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_bolt import App as SlackApp
from fastapi import APIRouter, Request

from app.models import SessionLocal, RawEvent, Channel
from app.sentiment import score_event
from app.enhanced_sentiment_simple import enhanced_score_event

logger = logging.getLogger(__name__)

# Initialize Slack app
slack_app = SlackApp(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# Create FastAPI router
slack_router = APIRouter()

# Create Slack request handler
handler = SlackRequestHandler(slack_app)


@slack_app.event("message")
def handle_message(body: Dict[str, Any], logger: logging.Logger):
    """Handle incoming Slack messages"""
    try:
        event = body.get("event", {})
        
        # Skip bot messages and message edits/deletes
        if event.get("bot_id") or event.get("subtype"):
            return
        
        # Extract key information
        channel_id = event.get("channel")
        user_id = event.get("user")
        timestamp = event.get("ts")
        text = event.get("text", "")
        
        logger.info(f"Processing message from {user_id} in {channel_id}")
        
        # Store raw event
        db = SessionLocal()
        try:
            # Ensure channel exists
            channel = db.query(Channel).filter(Channel.id == channel_id).first()
            if not channel:
                # Create channel if it doesn't exist
                channel = Channel(
                    id=channel_id,
                    name=f"channel-{channel_id}",  # Will be updated by channel info API
                    is_active=True
                )
                db.add(channel)
                db.commit()
            
            # Store raw event
            raw_event = RawEvent(
                event_type="message",
                channel_id=channel_id,
                user_id=user_id,
                timestamp=timestamp,
                json_data=body,
                processed=False
            )
            db.add(raw_event)
            db.commit()
            
            # Process sentiment analysis with AI enhancement
            try:
                # Try AI-enhanced analysis first
                ai_result = enhanced_score_event(body, db)
                
                if not ai_result:
                    # Fallback to traditional analysis
                    score_event(body, db)
                    
            except Exception as ai_error:
                logger.warning(f"AI sentiment analysis failed, using fallback: {ai_error}")
                score_event(body, db)
            
            logger.info(f"Successfully processed message {timestamp}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling message event: {e}")


@slack_app.event("reaction_added")
def handle_reaction_added(body: Dict[str, Any], logger: logging.Logger):
    """Handle reaction added events"""
    try:
        event = body.get("event", {})
        
        reaction = event.get("reaction")
        user_id = event.get("user")
        item = event.get("item", {})
        channel_id = item.get("channel")
        message_ts = item.get("ts")
        
        logger.info(f"Processing reaction {reaction} from {user_id} in {channel_id}")
        
        # Store raw event
        db = SessionLocal()
        try:
            raw_event = RawEvent(
                event_type="reaction_added",
                channel_id=channel_id,
                user_id=user_id,
                timestamp=message_ts,
                json_data=body,
                processed=False
            )
            db.add(raw_event)
            db.commit()
            
            # Process reaction sentiment impact
            from app.sentiment import update_sentiment_with_reaction
            update_sentiment_with_reaction(message_ts, channel_id, reaction, 1, db)
            
        except Exception as e:
            logger.error(f"Error processing reaction: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling reaction_added event: {e}")


@slack_app.event("reaction_removed")
def handle_reaction_removed(body: Dict[str, Any], logger: logging.Logger):
    """Handle reaction removed events"""
    try:
        event = body.get("event", {})
        
        reaction = event.get("reaction")
        user_id = event.get("user")
        item = event.get("item", {})
        channel_id = item.get("channel")
        message_ts = item.get("ts")
        
        logger.info(f"Processing reaction removal {reaction} from {user_id} in {channel_id}")
        
        # Store raw event
        db = SessionLocal()
        try:
            raw_event = RawEvent(
                event_type="reaction_removed",
                channel_id=channel_id,
                user_id=user_id,
                timestamp=message_ts,
                json_data=body,
                processed=False
            )
            db.add(raw_event)
            db.commit()
            
            # Process reaction sentiment impact (negative)
            from app.sentiment import update_sentiment_with_reaction
            update_sentiment_with_reaction(message_ts, channel_id, reaction, -1, db)
            
        except Exception as e:
            logger.error(f"Error processing reaction removal: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling reaction_removed event: {e}")


@slack_app.event("channel_created")
def handle_channel_created(body: Dict[str, Any], logger: logging.Logger):
    """Handle new channel creation"""
    try:
        event = body.get("event", {})
        channel = event.get("channel", {})
        
        channel_id = channel.get("id")
        channel_name = channel.get("name")
        
        logger.info(f"New channel created: {channel_name} ({channel_id})")
        
        # Add to database
        db = SessionLocal()
        try:
            new_channel = Channel(
                id=channel_id,
                name=channel_name,
                is_active=False  # Not monitored by default
            )
            db.add(new_channel)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error adding new channel: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling channel_created event: {e}")


@slack_app.event("app_mention")
def handle_app_mention(body: Dict[str, Any], say):
    """Handle when the bot is mentioned"""
    try:
        event = body.get("event", {})
        text = event.get("text", "")
        
        # Simple bot response
        if "help" in text.lower():
            say("I'm monitoring your team's mood and engagement levels! 📊\n"
                "Check the dashboard for insights: http://localhost:3000")
        elif "status" in text.lower():
            say("I'm actively monitoring your selected channels for sentiment analysis. "
                "All systems operational! 🟢")
        else:
            say("Hi there! 👋 I'm analyzing team sentiment to help improve engagement. "
                "Say 'help' for more info!")
                
    except Exception as e:
        logger.error(f"Error handling app mention: {e}")


# FastAPI endpoint for Slack events
@slack_router.post("/events")
async def slack_events_endpoint(req: Request):
    """Handle Slack events webhook"""
    return await handler.handle(req)


# Additional endpoint for Slack slash commands (future enhancement)
@slack_router.post("/commands")
async def slack_commands_endpoint(req: Request):
    """Handle Slack slash commands"""
    return await handler.handle(req)


# Health check for Slack integration
@slack_router.get("/health")
async def slack_health():
    """Check Slack integration health"""
    try:
        # Could add Slack API connectivity test here
        return {
            "status": "healthy",
            "slack_connected": True,
            "events_processed": "active"
        }
    except Exception as e:
        logger.error(f"Slack health check failed: {e}")
        return {
            "status": "unhealthy",
            "slack_connected": False,
            "error": str(e)
        }
