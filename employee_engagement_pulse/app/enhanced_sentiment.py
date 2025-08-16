"""
Enhanced AI-powered sentiment analysis using modern LLMs
Supports OpenAI, Anthropic, an    async def _analyze_with_openai(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze sentiment using OpenAI GPT"""
        import openai
        
        # Build context-aware prompt
        prompt = self._build_sentiment_prompt(text, context)
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=200
        )
        
        # Parse structured response
        result = response.choices[0].message.content
        return self._parse_ai_response(result)ls for better workplace understanding
"""
import os
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import asyncio

# Optional imports for different AI providers
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

from sqlalchemy.orm import Session
from app.models import Sentiment, RawEvent

logger = logging.getLogger(__name__)

class AISentimentAnalyzer:
    """Advanced AI-powered sentiment analysis"""
    
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        self.setup_ai_client()
    
    def setup_ai_client(self):
        """Initialize AI client based on provider"""
        if self.provider == "openai" and HAS_OPENAI:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.client = openai
            logger.info("Using OpenAI for sentiment analysis")
            
        elif self.provider == "anthropic" and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            logger.info("Using Anthropic Claude for sentiment analysis")
            
        elif self.provider == "huggingface" and HAS_TRANSFORMERS:
            # Use a specialized workplace sentiment model
            model_name = os.getenv("HF_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest")
            self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
            logger.info(f"Using Hugging Face model: {model_name}")
            
        else:
            logger.warning("No AI provider configured, falling back to VADER")
            self.client = None
    
    async def analyze_message_sentiment(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze sentiment with AI understanding of workplace context
        
        Args:
            text: The message text to analyze
            context: Additional context (channel, user, time, etc.)
            
        Returns:
            Dict with sentiment score, reasoning, and confidence
        """
        if not text.strip():
            return {"score": 0.0, "confidence": 0.0, "reasoning": "Empty message"}
        
        try:
            if self.provider == "openai" and self.client:
                return await self._analyze_with_openai(text, context)
            elif self.provider == "anthropic" and self.client:
                return await self._analyze_with_anthropic(text, context)
            elif self.provider == "huggingface":
                return await self._analyze_with_huggingface(text, context)
            else:
                return self._fallback_analysis(text)
                
        except Exception as e:
            logger.error(f"AI sentiment analysis failed: {e}")
            return self._fallback_analysis(text)
    
    async def _analyze_with_openai(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze sentiment using OpenAI GPT"""
        
        # Build context-aware prompt
        prompt = self._build_sentiment_prompt(text, context)
        
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=200
        )
        
        # Parse structured response
        result = response.choices[0].message.content
        return self._parse_ai_response(result)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI models"""
        return """You are an expert at analyzing workplace communication sentiment. 
        
Your task is to analyze Slack messages from software teams and return sentiment scores that help identify:
- Team morale and engagement
- Burnout risk indicators  
- Communication health
- Work-related stress or satisfaction

Consider:
- Workplace context (deploys, bugs, releases, meetings)
- Team communication patterns
- Sarcasm, humor, and informal language
- Technical jargon and abbreviations
- Emoji and reaction context

Return a JSON response with:
{
  "score": -1.0 to 1.0 (negative to positive),
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of the analysis",
  "indicators": ["key", "sentiment", "indicators"]
}"""
    
    def _build_sentiment_prompt(self, text: str, context: Dict[str, Any] = None) -> str:
        """Build context-aware prompt for sentiment analysis"""
        
        prompt = f"Analyze the sentiment of this workplace message:\n\nMessage: \"{text}\"\n\n"
        
        if context:
            if context.get('channel'):
                prompt += f"Channel: #{context['channel']}\n"
            if context.get('timestamp'):
                prompt += f"Time: {context['timestamp']}\n"
        
        prompt += "\nProvide sentiment analysis as JSON:"
        return prompt
    
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
            score = max(-1.0, min(1.0, score))  # Clamp to [-1, 1]
            
            return {
                "score": score,
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "AI analysis"),
                "indicators": result.get("indicators", [])
            }
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return {"score": 0.0, "confidence": 0.1, "reasoning": "Failed to parse AI response"}
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback to VADER when AI is unavailable"""
        try:
            from app.sentiment import analyze_text_sentiment, calculate_emoji_sentiment, calculate_keyword_sentiment
            
            # Use existing VADER-based analysis
            vader_scores = analyze_text_sentiment(text)
            emoji_boost = calculate_emoji_sentiment(text)
            keyword_boost = calculate_keyword_sentiment(text)
            
            final_score = vader_scores["compound"] + emoji_boost + keyword_boost
            final_score = max(-1.0, min(1.0, final_score))
            
            return {
                "score": final_score,
                "confidence": max(vader_scores["positive"], vader_scores["negative"]),
                "reasoning": "VADER + emoji/keyword analysis (AI unavailable)",
                "indicators": ["fallback_analysis"]
            }
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {"score": 0.0, "confidence": 0.1, "reasoning": "Analysis failed"}


# Global instance
ai_sentiment_analyzer = AISentimentAnalyzer()


async def enhanced_score_event(event_body: Dict[str, Any], db: Session) -> Optional[Sentiment]:
    """Enhanced AI-powered event scoring"""
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
        
        # Get AI analysis
        analysis = await ai_sentiment_analyzer.analyze_message_sentiment(text, context)
        
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
        
        logger.info(f"AI sentiment analysis: {analysis['score']:.3f} - {analysis['reasoning']}")
        return sentiment
        
    except Exception as e:
        logger.error(f"Enhanced sentiment analysis failed: {e}")
        db.rollback()
        return None
