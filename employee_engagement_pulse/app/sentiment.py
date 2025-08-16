"""
Sentiment analysis engine for Slack messages and reactions
"""
import os
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date

import nltk
try:
    import emoji
    HAS_EMOJI = True
except ImportError:
    HAS_EMOJI = False
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session

from app.models import Sentiment, RawEvent

logger = logging.getLogger(__name__)

# Download NLTK data if not present
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

# Initialize VADER sentiment analyzer
vader = SentimentIntensityAnalyzer()

# Emoji sentiment mappings
EMOJI_SCORES = {
    # Positive emojis
    "👍": 0.5, ":thumbsup:": 0.5, ":+1:": 0.5,
    "👎": -0.5, ":thumbsdown:": -0.5, ":-1:": -0.5,
    "🔥": 0.4, ":fire:": 0.4,
    "❤️": 0.6, ":heart:": 0.6,
    "😀": 0.4, ":grinning:": 0.4,
    "😊": 0.4, ":blush:": 0.4,
    "😃": 0.4, ":smiley:": 0.4,
    "😄": 0.4, ":smile:": 0.4,
    "🎉": 0.5, ":tada:": 0.5,
    "✅": 0.3, ":white_check_mark:": 0.3,
    "💯": 0.6, ":100:": 0.6,
    "🚀": 0.4, ":rocket:": 0.4,
    "⭐": 0.4, ":star:": 0.4,
    "💪": 0.4, ":muscle:": 0.4,
    
    # Negative emojis
    "😞": -0.4, ":disappointed:": -0.4,
    "😢": -0.5, ":cry:": -0.5,
    "😭": -0.6, ":sob:": -0.6,
    "😡": -0.6, ":rage:": -0.6,
    "😤": -0.4, ":huffing_with_anger:": -0.4,
    "😬": -0.2, ":grimacing:": -0.2,
    "😰": -0.4, ":cold_sweat:": -0.4,
    "😫": -0.5, ":tired_face:": -0.5,
    "💀": -0.3, ":skull:": -0.3,
    "❌": -0.3, ":x:": -0.3,
    "⚠️": -0.2, ":warning:": -0.2,
    
    # Neutral/thinking emojis
    "🤔": 0.0, ":thinking:": 0.0, ":thinking_face:": 0.0,
    "👀": 0.1, ":eyes:": 0.1,
    "🤷": 0.0, ":shrug:": 0.0,
    "🤖": 0.0, ":robot:": 0.0,
    
    # Work-related emojis
    "💻": 0.1, ":computer:": 0.1,
    "⚡": 0.2, ":zap:": 0.2,
    "🎯": 0.2, ":dart:": 0.2,
    "📊": 0.1, ":bar_chart:": 0.1,
    "🐛": -0.2, ":bug:": -0.2,
    "🔧": 0.0, ":wrench:": 0.0,
    "☕": 0.2, ":coffee:": 0.2,
    "🍕": 0.3, ":pizza:": 0.3,
}

# Reaction sentiment mappings (for reactions to messages)
REACTION_SCORES = {
    "thumbsup": 0.5,
    "+1": 0.5,
    "thumbsdown": -0.5,
    "-1": -0.5,
    "fire": 0.4,
    "heart": 0.6,
    "tada": 0.5,
    "100": 0.6,
    "rocket": 0.4,
    "star": 0.4,
    "eyes": 0.1,
    "thinking_face": 0.0,
    "x": -0.3,
    "warning": -0.2,
    "bug": -0.2,
    "coffee": 0.2,
    "pizza": 0.3,
}

# Work-related keywords and their sentiment modifiers
WORK_KEYWORDS = {
    # Positive work terms
    "deploy": 0.1,
    "shipped": 0.2,
    "release": 0.1,
    "launch": 0.2,
    "success": 0.3,
    "completed": 0.2,
    "fixed": 0.2,
    "resolved": 0.2,
    "great job": 0.4,
    "well done": 0.3,
    "awesome": 0.3,
    "excellent": 0.3,
    
    # Negative work terms
    "bug": -0.2,
    "error": -0.2,
    "failed": -0.3,
    "broken": -0.3,
    "issue": -0.1,
    "problem": -0.2,
    "incident": -0.3,
    "outage": -0.4,
    "down": -0.2,
    "crash": -0.3,
    "urgent": -0.1,
    "critical": -0.2,
    "blocke": -0.2,
    "stuck": -0.2,
    "frustrated": -0.4,
    "stressed": -0.4,
    "overwhelmed": -0.5,
    "burnout": -0.6,
    "tired": -0.2,
}


def extract_emojis(text: str) -> list:
    """Extract all emojis from text"""
    # Extract Unicode emojis
    if HAS_EMOJI:
        unicode_emojis = emoji.distinct_emoji_list(text)
    else:
        # Simple fallback - detect common emoji patterns
        unicode_emojis = re.findall(r'[😊😀🙂🎉👍✅😞😡😤😢👎❌🤔💯🔥❤️💪🚀]', text)
    
    # Extract Slack-style emojis (:emoji_name:)
    slack_emojis = re.findall(r':([^:\s]+):', text)
    slack_emojis = [f":{e}:" for e in slack_emojis]
    
    return unicode_emojis + slack_emojis


def calculate_emoji_sentiment(text: str) -> float:
    """Calculate sentiment boost from emojis in text"""
    emojis = extract_emojis(text)
    emoji_score = 0.0
    
    for emo in emojis:
        if emo in EMOJI_SCORES:
            emoji_score += EMOJI_SCORES[emo]
        elif emo.replace(':', '') in EMOJI_SCORES:
            # Handle :emoji: format
            emoji_score += EMOJI_SCORES[emo.replace(':', '')]
    
    # Normalize by number of emojis to prevent spam
    if len(emojis) > 0:
        emoji_score = emoji_score / max(len(emojis), 1)
    
    return min(max(emoji_score, -1.0), 1.0)  # Clamp between -1 and 1


def calculate_keyword_sentiment(text: str) -> float:
    """Calculate sentiment modifier based on work-related keywords"""
    text_lower = text.lower()
    keyword_score = 0.0
    
    for keyword, score in WORK_KEYWORDS.items():
        if keyword in text_lower:
            keyword_score += score
    
    return min(max(keyword_score, -0.5), 0.5)  # Limit keyword impact


def analyze_text_sentiment(text: str) -> Dict[str, float]:
    """Analyze sentiment of text using VADER"""
    if not text or not text.strip():
        return {
            "compound": 0.0,
            "positive": 0.0,
            "neutral": 1.0,
            "negative": 0.0
        }
    
    # Clean text for analysis (remove URLs, mentions, etc.)
    cleaned_text = re.sub(r'<@[UW][A-Z0-9]+>', '@user', text)  # Replace user mentions
    cleaned_text = re.sub(r'<#[C][A-Z0-9]+\|([^>]+)>', r'#\1', cleaned_text)  # Replace channel mentions
    cleaned_text = re.sub(r'<https?://[^>]+>', 'URL', cleaned_text)  # Replace URLs
    
    # Analyze with VADER
    scores = vader.polarity_scores(cleaned_text)
    
    return scores


def score_event(event_body: Dict[str, Any], db: Session) -> Optional[Sentiment]:
    """Main function to score a Slack event and store sentiment"""
    try:
        event = event_body.get("event", {})
        event_type = event.get("type")
        
        if event_type != "message":
            return None
        
        # Extract message details
        channel_id = event.get("channel")
        user_id = event.get("user")
        timestamp = event.get("ts")
        text = event.get("text", "")
        
        # Skip if essential data is missing
        if not all([channel_id, user_id, timestamp]):
            logger.warning(f"Missing essential data for sentiment analysis: {event}")
            return None
        
        # Check if we already processed this message
        existing = db.query(Sentiment).filter(
            Sentiment.message_ts == timestamp,
            Sentiment.channel_id == channel_id
        ).first()
        
        if existing:
            logger.info(f"Sentiment already exists for message {timestamp}")
            return existing
        
        # Analyze text sentiment
        text_scores = analyze_text_sentiment(text)
        base_sentiment = text_scores["compound"]
        
        # Calculate emoji boost
        emoji_boost = calculate_emoji_sentiment(text)
        
        # Calculate keyword modifier
        keyword_modifier = calculate_keyword_sentiment(text)
        
        # Calculate final score
        final_score = base_sentiment + emoji_boost + keyword_modifier
        final_score = min(max(final_score, -1.0), 1.0)  # Clamp between -1 and 1
        
        # Create sentiment record
        sentiment = Sentiment(
            channel_id=channel_id,
            user_id=user_id,
            message_ts=timestamp,
            text_content=text[:500],  # Truncate for storage
            sentiment_score=base_sentiment,
            confidence=max(text_scores["positive"], text_scores["negative"]),
            emoji_boost=emoji_boost,
            reaction_boost=0.0,  # Will be updated when reactions are added
            final_score=final_score,
            analysis_date=date.today()
        )
        
        db.add(sentiment)
        db.commit()
        
        logger.info(f"Sentiment analyzed for message {timestamp}: {final_score:.3f}")
        return sentiment
        
    except Exception as e:
        logger.error(f"Error scoring event: {e}")
        db.rollback()
        return None


def update_sentiment_with_reaction(message_ts: str, channel_id: str, reaction: str, 
                                 modifier: int, db: Session) -> bool:
    """Update existing sentiment with reaction data"""
    try:
        # Find existing sentiment record
        sentiment = db.query(Sentiment).filter(
            Sentiment.message_ts == message_ts,
            Sentiment.channel_id == channel_id
        ).first()
        
        if not sentiment:
            logger.warning(f"No sentiment record found for message {message_ts}")
            return False
        
        # Calculate reaction impact
        reaction_score = REACTION_SCORES.get(reaction, 0.0) * modifier
        
        # Update reaction boost (cumulative)
        sentiment.reaction_boost += reaction_score
        
        # Recalculate final score
        sentiment.final_score = (
            sentiment.sentiment_score + 
            sentiment.emoji_boost + 
            sentiment.reaction_boost
        )
        sentiment.final_score = min(max(sentiment.final_score, -1.0), 1.0)
        
        db.commit()
        
        logger.info(f"Updated sentiment for message {message_ts} with reaction {reaction}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating sentiment with reaction: {e}")
        db.rollback()
        return False


def get_sentiment_summary(channel_id: str, start_date: date, end_date: date, 
                         db: Session) -> Dict[str, Any]:
    """Get sentiment summary for a channel within date range"""
    try:
        sentiments = db.query(Sentiment).filter(
            Sentiment.channel_id == channel_id,
            Sentiment.analysis_date >= start_date,
            Sentiment.analysis_date <= end_date
        ).all()
        
        if not sentiments:
            return {
                "message_count": 0,
                "average_sentiment": 0.0,
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0
            }
        
        # Calculate summary statistics
        scores = [s.final_score for s in sentiments]
        avg_sentiment = sum(scores) / len(scores)
        
        positive_count = sum(1 for score in scores if score > 0.1)
        neutral_count = sum(1 for score in scores if -0.1 <= score <= 0.1)
        negative_count = sum(1 for score in scores if score < -0.1)
        
        return {
            "message_count": len(sentiments),
            "average_sentiment": round(avg_sentiment, 3),
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "sentiment_trend": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {e}")
        return {
            "message_count": 0,
            "average_sentiment": 0.0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "error": str(e)
        }
