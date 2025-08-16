"""
Enhanced AI-powered sentiment analysis using transformer models
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date

import torch
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    pipeline, RobertaTokenizer, RobertaForSequenceClassification
)
import numpy as np
from sklearn.preprocessing import StandardScaler

from app.models import Sentiment, RawEvent
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class AIEnhancedSentimentAnalyzer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load pre-trained models
        self.load_models()
        
        # Workplace-specific context understanding
        self.workplace_context = {
            'stress_indicators': ['deadline', 'overtime', 'crunch', 'pressure'],
            'collaboration_indicators': ['team', 'together', 'help', 'support'],
            'achievement_indicators': ['shipped', 'completed', 'success', 'milestone'],
            'technical_indicators': ['deploy', 'bug', 'fix', 'feature', 'code']
        }
    
    def load_models(self):
        """Load multiple specialized models"""
        try:
            # 1. General sentiment (RoBERTa fine-tuned)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # 2. Emotion detection (workplace emotions)
            self.emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # 3. Stress/Burnout detection (custom fine-tuned model)
            self.stress_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            
            # 4. Context understanding (workplace communication)
            self.context_pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ All AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading AI models: {e}")
            # Fallback to simpler models
            self.load_fallback_models()
    
    def load_fallback_models(self):
        """Load simpler models if advanced ones fail"""
        try:
            self.sentiment_pipeline = pipeline("sentiment-analysis", device=-1)
            self.emotion_pipeline = None
            self.context_pipeline = None
            logger.warning("⚠️ Using fallback sentiment model")
        except Exception as e:
            logger.error(f"Even fallback models failed: {e}")
            raise
    
    def analyze_message(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive AI analysis of a message
        """
        results = {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'emotions': {},
            'workplace_context': {},
            'risk_factors': {},
            'ai_insights': []
        }
        
        try:
            # 1. Advanced sentiment analysis
            sentiment_result = self.sentiment_pipeline(text)
            results['sentiment_raw'] = sentiment_result
            
            # Convert to our -1 to +1 scale
            if sentiment_result[0]['label'] == 'POSITIVE':
                results['sentiment_score'] = sentiment_result[0]['score']
            elif sentiment_result[0]['label'] == 'NEGATIVE':
                results['sentiment_score'] = -sentiment_result[0]['score']
            else:  # NEUTRAL
                results['sentiment_score'] = 0.0
            
            results['confidence'] = sentiment_result[0]['score']
            
            # 2. Emotion detection
            if self.emotion_pipeline:
                emotion_result = self.emotion_pipeline(text)
                results['emotions'] = {
                    'primary_emotion': emotion_result[0]['label'],
                    'emotion_confidence': emotion_result[0]['score'],
                    'all_emotions': emotion_result
                }
                
                # Detect burnout/stress emotions
                stress_emotions = ['sadness', 'anger', 'fear', 'disgust']
                if emotion_result[0]['label'] in stress_emotions:
                    results['risk_factors']['emotional_stress'] = emotion_result[0]['score']
            
            # 3. Workplace context analysis
            if self.context_pipeline:
                workplace_labels = [
                    'work stress', 'team collaboration', 'technical discussion',
                    'achievement celebration', 'problem solving', 'deadline pressure'
                ]
                
                context_result = self.context_pipeline(text, workplace_labels)
                results['workplace_context'] = {
                    'primary_context': context_result['labels'][0],
                    'context_confidence': context_result['scores'][0],
                    'all_contexts': dict(zip(context_result['labels'], context_result['scores']))
                }
            
            # 4. Advanced pattern recognition
            results['patterns'] = self.detect_patterns(text)
            
            # 5. Risk assessment
            results['risk_factors'].update(self.assess_risks(text, results))
            
            # 6. Generate AI insights
            results['ai_insights'] = self.generate_insights(text, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            # Return basic analysis
            return self.fallback_analysis(text)
    
    def detect_patterns(self, text: str) -> Dict[str, Any]:
        """Detect communication patterns using NLP"""
        patterns = {}
        
        # Time-based stress indicators
        time_pressure = ['asap', 'urgent', 'deadline', 'rush', 'quickly']
        patterns['time_pressure_score'] = sum(1 for word in time_pressure if word in text.lower()) / len(time_pressure)
        
        # Collaboration indicators
        collab_words = ['team', 'together', 'help', 'support', 'collaborate']
        patterns['collaboration_score'] = sum(1 for word in collab_words if word in text.lower()) / len(collab_words)
        
        # Technical complexity
        tech_words = ['bug', 'error', 'fix', 'deploy', 'code', 'system', 'server']
        patterns['technical_complexity'] = sum(1 for word in tech_words if word in text.lower()) / len(tech_words)
        
        # Communication style
        patterns['question_marks'] = text.count('?')
        patterns['exclamation_marks'] = text.count('!')
        patterns['message_length'] = len(text)
        patterns['word_count'] = len(text.split())
        
        return patterns
    
    def assess_risks(self, text: str, analysis_results: Dict[str, Any]) -> Dict[str, float]:
        """AI-powered risk assessment for burnout/engagement"""
        risks = {}
        
        # Sentiment-based risk
        sentiment_score = analysis_results.get('sentiment_score', 0)
        if sentiment_score < -0.3:
            risks['negative_sentiment_risk'] = abs(sentiment_score)
        
        # Emotional stress risk
        emotions = analysis_results.get('emotions', {})
        if emotions.get('primary_emotion') in ['sadness', 'anger', 'fear']:
            risks['emotional_distress'] = emotions.get('emotion_confidence', 0)
        
        # Workplace context risks
        context = analysis_results.get('workplace_context', {})
        if context.get('primary_context') in ['work stress', 'deadline pressure']:
            risks['work_pressure'] = context.get('context_confidence', 0)
        
        # Pattern-based risks
        patterns = analysis_results.get('patterns', {})
        if patterns.get('time_pressure_score', 0) > 0.3:
            risks['time_pressure'] = patterns['time_pressure_score']
        
        # Calculate overall risk score
        if risks:
            risks['overall_risk_score'] = sum(risks.values()) / len(risks)
        else:
            risks['overall_risk_score'] = 0.0
        
        return risks
    
    def generate_insights(self, text: str, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate AI-powered insights and recommendations"""
        insights = []
        
        sentiment = analysis_results.get('sentiment_score', 0)
        risks = analysis_results.get('risk_factors', {})
        emotions = analysis_results.get('emotions', {})
        context = analysis_results.get('workplace_context', {})
        
        # Sentiment insights
        if sentiment > 0.5:
            insights.append("🎉 High positive sentiment detected - great team morale indicator")
        elif sentiment < -0.5:
            insights.append("⚠️ Strong negative sentiment - may need management attention")
        
        # Emotional insights
        if emotions.get('primary_emotion') == 'joy' and emotions.get('emotion_confidence', 0) > 0.8:
            insights.append("😊 Team member expressing genuine happiness - positive engagement")
        elif emotions.get('primary_emotion') in ['sadness', 'anger'] and emotions.get('emotion_confidence', 0) > 0.7:
            insights.append(f"😔 Strong {emotions['primary_emotion']} detected - consider one-on-one check-in")
        
        # Context insights
        if context.get('primary_context') == 'deadline pressure' and context.get('context_confidence', 0) > 0.8:
            insights.append("📅 High deadline pressure detected - monitor for burnout signs")
        elif context.get('primary_context') == 'team collaboration' and context.get('context_confidence', 0) > 0.7:
            insights.append("🤝 Strong collaboration signals - healthy team dynamic")
        
        # Risk insights
        overall_risk = risks.get('overall_risk_score', 0)
        if overall_risk > 0.6:
            insights.append("🚨 High risk profile - recommend immediate intervention")
        elif overall_risk > 0.3:
            insights.append("⚠️ Moderate risk detected - monitor closely")
        
        return insights
    
    def fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Simple analysis if AI models fail"""
        # Basic keyword-based analysis as fallback
        positive_words = ['good', 'great', 'awesome', 'success', 'happy']
        negative_words = ['bad', 'terrible', 'failed', 'angry', 'sad']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = 0.5
        elif neg_count > pos_count:
            sentiment = -0.5
        else:
            sentiment = 0.0
        
        return {
            'sentiment_score': sentiment,
            'confidence': 0.5,
            'ai_insights': ['Using fallback analysis - install transformers for better results'],
            'risk_factors': {'overall_risk_score': abs(sentiment) if sentiment < 0 else 0}
        }


# Enhanced scoring function using AI
def ai_score_event(event_body: Dict[str, Any], db: Session) -> Optional[Sentiment]:
    """AI-enhanced event scoring"""
    try:
        # Initialize AI analyzer
        analyzer = AIEnhancedSentimentAnalyzer()
        
        event = event_body.get("event", {})
        if event.get("type") != "message":
            return None
        
        # Extract message details
        channel_id = event.get("channel")
        user_id = event.get("user")
        timestamp = event.get("ts")
        text = event.get("text", "")
        
        if not all([channel_id, user_id, timestamp]):
            return None
        
        # AI Analysis
        ai_results = analyzer.analyze_message(text, {'channel_id': channel_id, 'user_id': user_id})
        
        # Store enhanced sentiment data
        sentiment = Sentiment(
            channel_id=channel_id,
            user_id=user_id,
            message_ts=timestamp,
            text_content=text[:500],
            sentiment_score=ai_results['sentiment_score'],
            confidence=ai_results['confidence'],
            emoji_boost=0.0,  # Could be enhanced with AI emoji understanding
            reaction_boost=0.0,
            final_score=ai_results['sentiment_score'],
            analysis_date=date.today(),
            # Store AI insights in JSON field (would need to add to model)
            # ai_metadata=ai_results
        )
        
        db.add(sentiment)
        db.commit()
        
        logger.info(f"AI sentiment analyzed: {ai_results['sentiment_score']:.3f} with insights: {len(ai_results['ai_insights'])}")
        return sentiment
        
    except Exception as e:
        logger.error(f"AI sentiment analysis failed: {e}")
        # Fallback to original method
        from app.sentiment import score_event
        return score_event(event_body, db)
