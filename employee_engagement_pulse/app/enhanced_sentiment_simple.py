"""
Enhanced AI-powered sentiment analysis using modern LLMs (Simplified Version)
"""
import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session

# Optional imports for different AI providers
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from app.models import Sentiment

logger = logging.getLogger(__name__)

class AISentimentAnalyzer:
    """Simplified AI-powered sentiment analysis"""
    
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        self.setup_ai_client()
    
    def setup_ai_client(self):
        """Initialize AI client"""
        if self.provider == "openai" and HAS_OPENAI:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("Using OpenAI for sentiment analysis")
        else:
            logger.warning("OpenAI not configured, falling back to VADER")
            self.client = None
    
    def analyze_message_sentiment(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze sentiment with AI understanding"""
        if not text.strip():
            return {"score": 0.0, "confidence": 0.0, "reasoning": "Empty message"}
        
        try:
            if self.provider == "openai" and self.client and os.getenv("OPENAI_API_KEY"):
                return self._analyze_with_openai(text, context)
            else:
                return self._fallback_analysis(text)
                
        except Exception as e:
            logger.error(f"AI sentiment analysis failed: {e}")
            return self._fallback_analysis(text)
    
    def _analyze_with_openai(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze sentiment using OpenAI GPT"""
        
        system_prompt = """You are an expert at analyzing workplace communication sentiment. 
        
Analyze Slack messages from software teams and return sentiment scores that help identify team morale, burnout risk, and communication health.

Consider workplace context, sarcasm, technical jargon, and team dynamics.

Return a JSON response with:
{
  "score": -1.0 to 1.0 (negative to positive),
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation",
  "indicators": ["key", "sentiment", "indicators"]
}"""
        
        user_prompt = f"Analyze the sentiment of this workplace message: \"{text}\""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        return self._parse_ai_response(result)
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            result = json.loads(json_str)
            
            # Validate and normalize
            score = float(result.get("score", 0.0))
            score = max(-1.0, min(1.0, score))
            
            return {
                "score": score,
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "AI analysis"),
                "indicators": result.get("indicators", [])
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return {"score": 0.0, "confidence": 0.1, "reasoning": "Failed to parse AI response"}
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback to VADER when AI is unavailable"""
        try:
            from app.sentiment import analyze_text_sentiment
            
            # Use basic VADER analysis
            vader_scores = analyze_text_sentiment(text)
            final_score = vader_scores["compound"]
            
            # Simple emoji detection without library
            emoji_boost = 0.0
            if any(emoji in text for emoji in ['😊', '🙂', '😀', '🎉', '👍', '✅']):
                emoji_boost = 0.2
            elif any(emoji in text for emoji in ['😞', '😡', '😤', '😢', '👎', '❌']):
                emoji_boost = -0.2
            
            # Simple keyword boost
            keyword_boost = 0.0
            positive_keywords = ['great', 'good', 'excellent', 'awesome', 'thanks', 'love']
            negative_keywords = ['terrible', 'awful', 'hate', 'frustrated', 'annoying', 'broken']
            
            text_lower = text.lower()
            for word in positive_keywords:
                if word in text_lower:
                    keyword_boost += 0.1
            for word in negative_keywords:
                if word in text_lower:
                    keyword_boost -= 0.1
            
            final_score = final_score + emoji_boost + keyword_boost
            final_score = max(-1.0, min(1.0, final_score))
            
            return {
                "score": final_score,
                "confidence": max(vader_scores.get("positive", 0.5), vader_scores.get("negative", 0.5)),
                "reasoning": f"VADER analysis (score: {vader_scores['compound']:.2f}) with basic emoji/keyword detection",
                "indicators": ["vader_fallback"]
            }
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {"score": 0.0, "confidence": 0.1, "reasoning": f"Fallback analysis failed: {str(e)}"}


# Global instance
ai_sentiment_analyzer = AISentimentAnalyzer()


def enhanced_score_event(event_body: Dict[str, Any], db: Session) -> Optional[Sentiment]:
    """Enhanced AI-powered event scoring (synchronous version)"""
    try:
        event = event_body.get("event", {})
        if event.get("type") != "message":
            return None
        
        # Extract data
        channel_id = event.get("channel")
        user_id = event.get("user")
        timestamp = event.get("ts")
        text = event.get("text", "")
        
        if not all([channel_id, user_id, timestamp]):
            return None
        
        # Check if already processed
        existing = db.query(Sentiment).filter(
            Sentiment.message_ts == timestamp,
            Sentiment.channel_id == channel_id
        ).first()
        
        if existing:
            return existing
        
        # Build context for AI
        context = {
            "channel": channel_id,
            "user": user_id,
            "timestamp": timestamp
        }
        
        # Get AI analysis (synchronous)
        analysis = ai_sentiment_analyzer.analyze_message_sentiment(text, context)
        
        # Create sentiment record
        sentiment = Sentiment(
            channel_id=channel_id,
            user_id=user_id,
            message_ts=timestamp,
            text_content=text[:500],
            sentiment_score=analysis["score"],
            confidence=analysis["confidence"],
            emoji_boost=0.0,  # AI handles this internally
            reaction_boost=0.0,
            final_score=analysis["score"],
            analysis_date=date.today()
        )
        
        db.add(sentiment)
        db.commit()
        
        logger.info(f"AI sentiment: {analysis['score']:.3f} - {analysis['reasoning'][:50]}...")
        return sentiment
        
    except Exception as e:
        logger.error(f"Enhanced sentiment analysis failed: {e}")
        db.rollback()
        return None
