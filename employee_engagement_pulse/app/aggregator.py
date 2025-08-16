"""
Data aggregation engine for daily and weekly sentiment summaries
"""
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models import (
    SessionLocal, Sentiment, DailySummary, WeeklySummary, 
    Channel, Insight
)

logger = logging.getLogger(__name__)

# Configuration
SENTIMENT_THRESHOLD_NEGATIVE = float(os.getenv("SENTIMENT_THRESHOLD_NEGATIVE", -0.1))
BURNOUT_DELTA_THRESHOLD = float(os.getenv("BURNOUT_DELTA_THRESHOLD", -0.2))


def get_monday_of_week(target_date: date) -> date:
    """Get the Monday of the week for a given date"""
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)
    return monday


def get_sunday_of_week(target_date: date) -> date:
    """Get the Sunday of the week for a given date"""
    monday = get_monday_of_week(target_date)
    sunday = monday + timedelta(days=6)
    return sunday


def create_daily_summary(channel_id: str, summary_date: date, db: Session) -> Optional[DailySummary]:
    """Create daily summary for a specific channel and date"""
    try:
        # Check if summary already exists
        existing = db.query(DailySummary).filter(
            DailySummary.channel_id == channel_id,
            DailySummary.summary_date == summary_date
        ).first()
        
        if existing:
            logger.info(f"Daily summary already exists for {channel_id} on {summary_date}")
            return existing
        
        # Get sentiments for the day
        sentiments = db.query(Sentiment).filter(
            Sentiment.channel_id == channel_id,
            Sentiment.analysis_date == summary_date
        ).all()
        
        if not sentiments:
            logger.info(f"No sentiments found for {channel_id} on {summary_date}")
            return None
        
        # Calculate statistics
        scores = [s.final_score for s in sentiments]
        avg_sentiment = sum(scores) / len(scores)
        
        positive_count = sum(1 for score in scores if score > 0.1)
        neutral_count = sum(1 for score in scores if -0.1 <= score <= 0.1)
        negative_count = sum(1 for score in scores if score < -0.1)
        
        # Find most active users
        user_counts = defaultdict(int)
        for sentiment in sentiments:
            if sentiment.user_id:
                user_counts[sentiment.user_id] += 1
        
        # Top 5 most active users
        most_active = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_active_users = [{"user_id": user, "message_count": count} for user, count in most_active]
        
        # Calculate peak activity hour (simplified - would need timestamp parsing for real implementation)
        peak_activity_hour = 14  # Default to 2 PM (would calculate from actual timestamps)
        
        # Create summary record
        summary = DailySummary(
            channel_id=channel_id,
            summary_date=summary_date,
            message_count=len(sentiments),
            avg_sentiment=round(avg_sentiment, 3),
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            most_active_users=most_active_users,
            peak_activity_hour=peak_activity_hour
        )
        
        db.add(summary)
        db.commit()
        
        logger.info(f"Created daily summary for {channel_id} on {summary_date}: avg={avg_sentiment:.3f}")
        return summary
        
    except Exception as e:
        logger.error(f"Error creating daily summary: {e}")
        db.rollback()
        return None


def create_weekly_summary(channel_id: str, week_start: date, db: Session) -> Optional[WeeklySummary]:
    """Create weekly summary for a specific channel and week"""
    try:
        week_end = week_start + timedelta(days=6)
        
        # Check if summary already exists
        existing = db.query(WeeklySummary).filter(
            WeeklySummary.channel_id == channel_id,
            WeeklySummary.week_start == week_start
        ).first()
        
        if existing:
            logger.info(f"Weekly summary already exists for {channel_id} week {week_start}")
            return existing
        
        # Get sentiments for the week
        sentiments = db.query(Sentiment).filter(
            Sentiment.channel_id == channel_id,
            and_(
                Sentiment.analysis_date >= week_start,
                Sentiment.analysis_date <= week_end
            )
        ).all()
        
        if not sentiments:
            logger.info(f"No sentiments found for {channel_id} week {week_start}")
            return None
        
        # Calculate weekly statistics
        scores = [s.final_score for s in sentiments]
        avg_sentiment = sum(scores) / len(scores)
        
        # Get previous week's average for trend calculation
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = prev_week_start + timedelta(days=6)
        
        prev_week_sentiments = db.query(Sentiment).filter(
            Sentiment.channel_id == channel_id,
            and_(
                Sentiment.analysis_date >= prev_week_start,
                Sentiment.analysis_date <= prev_week_end
            )
        ).all()
        
        sentiment_trend = 0.0
        if prev_week_sentiments:
            prev_scores = [s.final_score for s in prev_week_sentiments]
            prev_avg = sum(prev_scores) / len(prev_scores)
            sentiment_trend = avg_sentiment - prev_avg
        
        # Determine burnout flag
        burnout_flag = (
            sentiment_trend <= BURNOUT_DELTA_THRESHOLD or 
            avg_sentiment <= SENTIMENT_THRESHOLD_NEGATIVE
        )
        
        # Determine engagement level
        if avg_sentiment >= 0.3:
            engagement_level = "High"
        elif avg_sentiment >= 0.1:
            engagement_level = "Medium"
        elif avg_sentiment >= -0.1:
            engagement_level = "Low"
        else:
            engagement_level = "Critical"
        
        # Count unique active users
        unique_users = set(s.user_id for s in sentiments if s.user_id)
        active_user_count = len(unique_users)
        
        # Analyze top topics (simplified - would use NLP for real implementation)
        top_topics = ["deployment", "code review", "bug fix", "planning", "team meeting"]  # Mock data
        
        # Create summary record
        summary = WeeklySummary(
            channel_id=channel_id,
            week_start=week_start,
            week_end=week_end,
            message_count=len(sentiments),
            avg_sentiment=round(avg_sentiment, 3),
            sentiment_trend=round(sentiment_trend, 3),
            burnout_flag=burnout_flag,
            engagement_level=engagement_level,
            top_topics=top_topics,
            active_user_count=active_user_count
        )
        
        db.add(summary)
        db.commit()
        
        logger.info(f"Created weekly summary for {channel_id} week {week_start}: "
                   f"avg={avg_sentiment:.3f}, trend={sentiment_trend:.3f}, burnout={burnout_flag}")
        
        # Generate insights if needed
        if burnout_flag:
            generate_burnout_insight(channel_id, summary, db)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error creating weekly summary: {e}")
        db.rollback()
        return None


def generate_burnout_insight(channel_id: str, weekly_summary: WeeklySummary, db: Session):
    """Generate burnout warning insight"""
    try:
        # Check if we already have a recent burnout insight
        recent_insight = db.query(Insight).filter(
            Insight.channel_id == channel_id,
            Insight.insight_type == "burnout_alert",
            Insight.is_active == True,
            Insight.created_at >= datetime.now() - timedelta(days=7)
        ).first()
        
        if recent_insight:
            logger.info(f"Recent burnout insight already exists for {channel_id}")
            return
        
        # Determine severity based on sentiment levels
        avg_sentiment = weekly_summary.avg_sentiment
        sentiment_trend = weekly_summary.sentiment_trend
        
        if avg_sentiment <= -0.3 or sentiment_trend <= -0.3:
            severity = "critical"
            title = "Critical Team Burnout Detected"
        elif avg_sentiment <= -0.2 or sentiment_trend <= -0.25:
            severity = "high"
            title = "High Risk of Team Burnout"
        else:
            severity = "medium"
            title = "Team Sentiment Declining"
        
        # Create description and recommendation
        description = (
            f"Team sentiment in this channel has declined significantly. "
            f"Current average sentiment: {avg_sentiment:.2f}, "
            f"trend over past week: {sentiment_trend:+.2f}. "
            f"Engagement level: {weekly_summary.engagement_level}."
        )
        
        recommendations = []
        if avg_sentiment <= -0.2:
            recommendations.append("Schedule a team check-in to discuss workload and stress levels")
        if sentiment_trend <= -0.25:
            recommendations.append("Investigate recent changes that may have impacted team morale")
        if weekly_summary.active_user_count < 5:
            recommendations.append("Low participation detected - consider improving team engagement")
        
        recommendation = ". ".join(recommendations) if recommendations else "Monitor closely and consider team intervention"
        
        # Create insight
        insight = Insight(
            channel_id=channel_id,
            insight_type="burnout_alert",
            title=title,
            description=description,
            severity=severity,
            actionable=True,
            recommendation=recommendation,
            data_source={
                "avg_sentiment": avg_sentiment,
                "sentiment_trend": sentiment_trend,
                "message_count": weekly_summary.message_count,
                "active_user_count": weekly_summary.active_user_count,
                "week_start": weekly_summary.week_start.isoformat(),
                "week_end": weekly_summary.week_end.isoformat()
            },
            is_active=True
        )
        
        db.add(insight)
        db.commit()
        
        logger.info(f"Generated burnout insight for {channel_id}: {severity}")
        
    except Exception as e:
        logger.error(f"Error generating burnout insight: {e}")
        db.rollback()


def run_daily_aggregation_job():
    """Run daily aggregation for all active channels"""
    logger.info("Starting daily aggregation job")
    
    db = SessionLocal()
    try:
        # Get yesterday's date
        yesterday = date.today() - timedelta(days=1)
        
        # Get all active channels
        active_channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        summaries_created = 0
        for channel in active_channels:
            summary = create_daily_summary(channel.id, yesterday, db)
            if summary:
                summaries_created += 1
        
        logger.info(f"Daily aggregation completed: {summaries_created} summaries created")
        
    except Exception as e:
        logger.error(f"Error in daily aggregation job: {e}")
    finally:
        db.close()


def run_weekly_aggregation_job():
    """Run weekly aggregation for all active channels"""
    logger.info("Starting weekly aggregation job")
    
    db = SessionLocal()
    try:
        # Get last week's Monday
        today = date.today()
        last_monday = get_monday_of_week(today) - timedelta(days=7)
        
        # Get all active channels
        active_channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        summaries_created = 0
        for channel in active_channels:
            summary = create_weekly_summary(channel.id, last_monday, db)
            if summary:
                summaries_created += 1
        
        logger.info(f"Weekly aggregation completed: {summaries_created} summaries created")
        
    except Exception as e:
        logger.error(f"Error in weekly aggregation job: {e}")
    finally:
        db.close()


def backfill_summaries(start_date: date, end_date: date, channel_ids: Optional[List[str]] = None):
    """Backfill daily and weekly summaries for a date range"""
    logger.info(f"Starting backfill from {start_date} to {end_date}")
    
    db = SessionLocal()
    try:
        # Get channels to process
        if channel_ids:
            channels = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
        else:
            channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        current_date = start_date
        daily_summaries_created = 0
        weekly_summaries_created = 0
        
        # Process each date in range
        while current_date <= end_date:
            # Create daily summaries
            for channel in channels:
                summary = create_daily_summary(channel.id, current_date, db)
                if summary:
                    daily_summaries_created += 1
            
            # Create weekly summary if it's a Monday
            if current_date.weekday() == 0:  # Monday
                for channel in channels:
                    summary = create_weekly_summary(channel.id, current_date, db)
                    if summary:
                        weekly_summaries_created += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"Backfill completed: {daily_summaries_created} daily, "
                   f"{weekly_summaries_created} weekly summaries created")
        
    except Exception as e:
        logger.error(f"Error in backfill: {e}")
    finally:
        db.close()


def get_channel_trends(channel_id: str, days: int = 30) -> Dict[str, Any]:
    """Get sentiment trends for a channel over specified days"""
    db = SessionLocal()
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get daily summaries
        daily_summaries = db.query(DailySummary).filter(
            DailySummary.channel_id == channel_id,
            and_(
                DailySummary.summary_date >= start_date,
                DailySummary.summary_date <= end_date
            )
        ).order_by(DailySummary.summary_date).all()
        
        # Get weekly summaries
        weekly_summaries = db.query(WeeklySummary).filter(
            WeeklySummary.channel_id == channel_id,
            and_(
                WeeklySummary.week_start >= start_date,
                WeeklySummary.week_start <= end_date
            )
        ).order_by(WeeklySummary.week_start).all()
        
        return {
            "channel_id": channel_id,
            "period_days": days,
            "daily_trends": [
                {
                    "date": summary.summary_date.isoformat(),
                    "avg_sentiment": summary.avg_sentiment,
                    "message_count": summary.message_count,
                    "positive_count": summary.positive_count,
                    "negative_count": summary.negative_count
                }
                for summary in daily_summaries
            ],
            "weekly_trends": [
                {
                    "week_start": summary.week_start.isoformat(),
                    "week_end": summary.week_end.isoformat(),
                    "avg_sentiment": summary.avg_sentiment,
                    "sentiment_trend": summary.sentiment_trend,
                    "engagement_level": summary.engagement_level,
                    "burnout_flag": summary.burnout_flag,
                    "active_user_count": summary.active_user_count
                }
                for summary in weekly_summaries
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting channel trends: {e}")
        return {"error": str(e)}
    finally:
        db.close()
