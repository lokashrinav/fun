"""
Insight generation engine for actionable team engagement recommendations
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.models import (
    SessionLocal, Insight, WeeklySummary, DailySummary, 
    Sentiment, Channel, get_db
)

logger = logging.getLogger(__name__)


def generate_engagement_insights(channel_id: str, db: Session) -> List[Insight]:
    """Generate various engagement insights for a channel"""
    insights = []
    
    try:
        # Get recent data for analysis
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get weekly summaries for the past month
        weekly_summaries = db.query(WeeklySummary).filter(
            WeeklySummary.channel_id == channel_id,
            WeeklySummary.week_start >= start_date
        ).order_by(WeeklySummary.week_start.desc()).all()
        
        if not weekly_summaries:
            logger.info(f"No weekly summaries found for {channel_id}")
            return insights
        
        # Generate different types of insights
        insights.extend(_check_burnout_patterns(channel_id, weekly_summaries, db))
        insights.extend(_check_engagement_spikes(channel_id, weekly_summaries, db))
        insights.extend(_check_participation_trends(channel_id, weekly_summaries, db))
        insights.extend(_check_sentiment_volatility(channel_id, weekly_summaries, db))
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating engagement insights: {e}")
        return []


def _check_burnout_patterns(channel_id: str, weekly_summaries: List[WeeklySummary], 
                          db: Session) -> List[Insight]:
    """Check for burnout patterns and warning signs"""
    insights = []
    
    if len(weekly_summaries) < 2:
        return insights
    
    recent_weeks = weekly_summaries[:3]  # Last 3 weeks
    
    # Check for consecutive negative sentiment
    negative_weeks = sum(1 for w in recent_weeks if w.avg_sentiment < -0.1)
    
    if negative_weeks >= 2:
        severity = "critical" if negative_weeks == 3 else "high"
        
        insight = Insight(
            channel_id=channel_id,
            insight_type="burnout_pattern",
            title=f"Sustained Negative Sentiment Detected",
            description=f"Team sentiment has been negative for {negative_weeks} consecutive weeks. "
                       f"Average sentiment over this period: {sum(w.avg_sentiment for w in recent_weeks) / len(recent_weeks):.2f}",
            severity=severity,
            recommendation="Schedule immediate team check-in. Consider workload redistribution and stress management support.",
            data_source={
                "weeks_analyzed": len(recent_weeks),
                "negative_weeks": negative_weeks,
                "avg_sentiment_trend": [w.avg_sentiment for w in recent_weeks]
            }
        )
        insights.append(insight)
    
    # Check for declining participation
    if len(recent_weeks) >= 2:
        participation_trend = recent_weeks[0].active_user_count - recent_weeks[-1].active_user_count
        if participation_trend < -2:  # 2+ fewer active users
            insight = Insight(
                channel_id=channel_id,
                insight_type="participation_decline",
                title="Team Participation Declining",
                description=f"Active user participation has dropped by {abs(participation_trend)} users over recent weeks.",
                severity="medium",
                recommendation="Investigate barriers to participation. Consider team engagement activities.",
                data_source={
                    "participation_change": participation_trend,
                    "current_active_users": recent_weeks[0].active_user_count,
                    "previous_active_users": recent_weeks[-1].active_user_count
                }
            )
            insights.append(insight)
    
    return insights


def _check_engagement_spikes(channel_id: str, weekly_summaries: List[WeeklySummary], 
                           db: Session) -> List[Insight]:
    """Check for positive engagement spikes worth celebrating"""
    insights = []
    
    if len(weekly_summaries) < 2:
        return insights
    
    recent_week = weekly_summaries[0]
    previous_week = weekly_summaries[1] if len(weekly_summaries) > 1 else None
    
    # Check for significant positive sentiment spike
    if previous_week and recent_week.avg_sentiment > 0.3:
        sentiment_improvement = recent_week.avg_sentiment - previous_week.avg_sentiment
        
        if sentiment_improvement > 0.2:
            insight = Insight(
                channel_id=channel_id,
                insight_type="engagement_spike",
                title="Exceptional Team Morale Boost",
                description=f"Team sentiment has improved significantly by {sentiment_improvement:+.2f} points this week! "
                           f"Current sentiment: {recent_week.avg_sentiment:.2f}",
                severity="low",  # Positive insight
                recommendation="Identify and document what contributed to this positive change to replicate success.",
                data_source={
                    "sentiment_improvement": sentiment_improvement,
                    "current_sentiment": recent_week.avg_sentiment,
                    "previous_sentiment": previous_week.avg_sentiment
                }
            )
            insights.append(insight)
    
    # Check for high participation weeks
    if recent_week.active_user_count > 10:  # Threshold for "high participation"
        avg_participation = sum(w.active_user_count for w in weekly_summaries[:4]) / min(len(weekly_summaries), 4)
        
        if recent_week.active_user_count > avg_participation * 1.3:
            insight = Insight(
                channel_id=channel_id,
                insight_type="high_participation",
                title="Exceptional Team Participation",
                description=f"Team participation reached {recent_week.active_user_count} active users this week, "
                           f"{((recent_week.active_user_count / avg_participation - 1) * 100):.0f}% above average.",
                severity="low",
                recommendation="Celebrate this engagement! Consider what factors contributed to high participation.",
                data_source={
                    "current_participation": recent_week.active_user_count,
                    "average_participation": round(avg_participation, 1),
                    "improvement_percentage": round((recent_week.active_user_count / avg_participation - 1) * 100, 1)
                }
            )
            insights.append(insight)
    
    return insights


def _check_participation_trends(channel_id: str, weekly_summaries: List[WeeklySummary], 
                              db: Session) -> List[Insight]:
    """Analyze participation trends over time"""
    insights = []
    
    if len(weekly_summaries) < 3:
        return insights
    
    # Calculate participation trend over last 4 weeks
    participation_counts = [w.active_user_count for w in weekly_summaries[:4]]
    
    # Simple linear trend calculation
    weeks = list(range(len(participation_counts)))
    if len(weeks) > 1:
        # Calculate slope of participation trend
        n = len(weeks)
        sum_x = sum(weeks)
        sum_y = sum(participation_counts)
        sum_xy = sum(w * p for w, p in zip(weeks, participation_counts))
        sum_x2 = sum(w * w for w in weeks)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope < -0.5:  # Declining trend
            insight = Insight(
                channel_id=channel_id,
                insight_type="participation_trend",
                title="Declining Participation Trend",
                description=f"Team participation has been steadily declining over the past {len(participation_counts)} weeks.",
                severity="medium",
                recommendation="Investigate causes of reduced participation. Consider team surveys or one-on-ones.",
                data_source={
                    "trend_slope": round(slope, 2),
                    "participation_history": participation_counts,
                    "weeks_analyzed": len(participation_counts)
                }
            )
            insights.append(insight)
        elif slope > 0.5:  # Growing trend
            insight = Insight(
                channel_id=channel_id,
                insight_type="participation_growth",
                title="Growing Team Participation",
                description=f"Team participation has been steadily increasing over the past {len(participation_counts)} weeks.",
                severity="low",
                recommendation="Continue current engagement strategies. Document successful practices.",
                data_source={
                    "trend_slope": round(slope, 2),
                    "participation_history": participation_counts,
                    "weeks_analyzed": len(participation_counts)
                }
            )
            insights.append(insight)
    
    return insights


def _check_sentiment_volatility(channel_id: str, weekly_summaries: List[WeeklySummary], 
                              db: Session) -> List[Insight]:
    """Check for high sentiment volatility which might indicate instability"""
    insights = []
    
    if len(weekly_summaries) < 4:
        return insights
    
    recent_sentiments = [w.avg_sentiment for w in weekly_summaries[:4]]
    
    # Calculate standard deviation as measure of volatility
    mean_sentiment = sum(recent_sentiments) / len(recent_sentiments)
    variance = sum((s - mean_sentiment) ** 2 for s in recent_sentiments) / len(recent_sentiments)
    std_dev = variance ** 0.5
    
    if std_dev > 0.3:  # High volatility threshold
        insight = Insight(
            channel_id=channel_id,
            insight_type="sentiment_volatility",
            title="High Sentiment Volatility Detected",
            description=f"Team sentiment has been highly variable over recent weeks (std dev: {std_dev:.2f}). "
                       f"This may indicate instability or rapid changes in team dynamics.",
            severity="medium",
            recommendation="Investigate causes of sentiment swings. Consider more frequent team check-ins.",
            data_source={
                "volatility_score": round(std_dev, 3),
                "mean_sentiment": round(mean_sentiment, 3),
                "sentiment_history": recent_sentiments,
                "volatility_threshold": 0.3
            }
        )
        insights.append(insight)
    
    return insights


def generate_channel_recommendations(channel_id: str, db: Session) -> Dict[str, Any]:
    """Generate actionable recommendations for a specific channel"""
    try:
        # Get recent weekly summary
        recent_summary = db.query(WeeklySummary).filter(
            WeeklySummary.channel_id == channel_id
        ).order_by(WeeklySummary.week_start.desc()).first()
        
        if not recent_summary:
            return {"error": "No recent data available for recommendations"}
        
        recommendations = []
        priority_level = "low"
        
        # Analyze current state and generate recommendations
        if recent_summary.burnout_flag:
            priority_level = "high"
            recommendations.append({
                "type": "immediate_action",
                "title": "Address Burnout Risk",
                "description": "Schedule urgent team meeting to discuss workload and stress levels",
                "urgency": "high"
            })
        
        if recent_summary.avg_sentiment < -0.1:
            priority_level = max(priority_level, "medium")
            recommendations.append({
                "type": "sentiment_improvement",
                "title": "Improve Team Sentiment",
                "description": "Consider team building activities or recognition programs",
                "urgency": "medium"
            })
        
        if recent_summary.active_user_count < 5:
            recommendations.append({
                "type": "engagement_boost",
                "title": "Increase Participation",
                "description": "Encourage more team members to actively participate in discussions",
                "urgency": "medium"
            })
        
        if recent_summary.engagement_level == "High":
            recommendations.append({
                "type": "maintain_momentum",
                "title": "Maintain High Engagement",
                "description": "Document current successful practices and continue them",
                "urgency": "low"
            })
        
        return {
            "channel_id": channel_id,
            "current_state": {
                "engagement_level": recent_summary.engagement_level,
                "avg_sentiment": recent_summary.avg_sentiment,
                "burnout_flag": recent_summary.burnout_flag,
                "active_users": recent_summary.active_user_count
            },
            "priority_level": priority_level,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating channel recommendations: {e}")
        return {"error": str(e)}


def get_all_active_insights(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """Get all active insights across all channels"""
    try:
        insights = db.query(Insight).filter(
            Insight.is_active == True
        ).order_by(
            Insight.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for insight in insights:
            result.append({
                "id": insight.id,
                "channel_id": insight.channel_id,
                "type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "severity": insight.severity,
                "recommendation": insight.recommendation,
                "created_at": insight.created_at.isoformat(),
                "acknowledged": insight.acknowledged_by is not None,
                "acknowledged_by": insight.acknowledged_by,
                "data_source": insight.data_source
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting active insights: {e}")
        return []


def acknowledge_insight(insight_id: int, acknowledged_by: str, db: Session) -> bool:
    """Mark an insight as acknowledged"""
    try:
        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        
        if not insight:
            logger.warning(f"Insight {insight_id} not found")
            return False
        
        insight.acknowledged_by = acknowledged_by
        insight.acknowledged_at = datetime.now()
        insight.is_active = False  # Mark as resolved
        
        db.commit()
        logger.info(f"Insight {insight_id} acknowledged by {acknowledged_by}")
        return True
        
    except Exception as e:
        logger.error(f"Error acknowledging insight {insight_id}: {e}")
        db.rollback()
        return False


def run_insight_generation_job():
    """Run insight generation for all active channels"""
    logger.info("Starting insight generation job")
    
    db = SessionLocal()
    try:
        # Get all active channels
        from app.models import Channel
        active_channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        total_insights = 0
        for channel in active_channels:
            insights = generate_engagement_insights(channel.id, db)
            
            # Add insights to database
            for insight in insights:
                db.add(insight)
            
            total_insights += len(insights)
        
        db.commit()
        logger.info(f"Insight generation completed: {total_insights} insights generated")
        
    except Exception as e:
        logger.error(f"Error in insight generation job: {e}")
        db.rollback()
    finally:
        db.close()
