"""
FastAPI routes for the Employee Engagement Pulse API
"""
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models import get_db, Channel, DailySummary, WeeklySummary, Insight, Sentiment
from app.aggregator import get_channel_trends, backfill_summaries, run_daily_aggregation_job, run_weekly_aggregation_job
from app.insights import (
    generate_engagement_insights, generate_channel_recommendations, 
    get_all_active_insights, acknowledge_insight, run_insight_generation_job
)
from app.scheduler import get_scheduler_status, trigger_job_manually
from app.sentiment import get_sentiment_summary

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response validation
class ChannelCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class InsightAcknowledge(BaseModel):
    acknowledged_by: str


# Channel management endpoints
@router.get("/channels")
async def get_channels(
    active_only: bool = Query(True, description="Return only active channels"),
    db: Session = Depends(get_db)
):
    """Get all channels"""
    try:
        query = db.query(Channel)
        if active_only:
            query = query.filter(Channel.is_active == True)
        
        channels = query.all()
        
        return {
            "channels": [
                {
                    "id": ch.id,
                    "name": ch.name,
                    "description": ch.description,
                    "is_active": ch.is_active,
                    "created_at": ch.created_at.isoformat(),
                    "updated_at": ch.updated_at.isoformat()
                }
                for ch in channels
            ],
            "count": len(channels)
        }
        
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/channels")
async def create_channel(
    channel: ChannelCreate,
    db: Session = Depends(get_db)
):
    """Create a new channel"""
    try:
        # Check if channel already exists
        existing = db.query(Channel).filter(Channel.id == channel.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Channel already exists")
        
        new_channel = Channel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            is_active=channel.is_active
        )
        
        db.add(new_channel)
        db.commit()
        db.refresh(new_channel)
        
        return {
            "message": "Channel created successfully",
            "channel": {
                "id": new_channel.id,
                "name": new_channel.name,
                "description": new_channel.description,
                "is_active": new_channel.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/channels/{channel_id}")
async def update_channel(
    channel_id: str,
    updates: ChannelUpdate,
    db: Session = Depends(get_db)
):
    """Update a channel"""
    try:
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Apply updates
        if updates.name is not None:
            channel.name = updates.name
        if updates.description is not None:
            channel.description = updates.description
        if updates.is_active is not None:
            channel.is_active = updates.is_active
        
        channel.updated_at = datetime.now()
        db.commit()
        
        return {
            "message": "Channel updated successfully",
            "channel": {
                "id": channel.id,
                "name": channel.name,
                "description": channel.description,
                "is_active": channel.is_active,
                "updated_at": channel.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    db: Session = Depends(get_db)
):
    """Delete a channel"""
    try:
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        db.delete(channel)
        db.commit()
        
        return {"message": "Channel deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Sentiment and analytics endpoints
@router.get("/sentiment/{channel_id}")
async def get_channel_sentiment(
    channel_id: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get sentiment data for a specific channel"""
    try:
        # Verify channel exists
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Get sentiment trends
        trends = get_channel_trends(channel_id, days)
        
        # Get recent sentiment summary
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        summary = get_sentiment_summary(channel_id, start_date, end_date, db)
        
        return {
            "channel": {
                "id": channel.id,
                "name": channel.name
            },
            "period_days": days,
            "summary": summary,
            "trends": trends
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment")
async def get_all_sentiment(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    active_only: bool = Query(True, description="Only include active channels"),
    db: Session = Depends(get_db)
):
    """Get sentiment overview for all channels"""
    try:
        query = db.query(Channel)
        if active_only:
            query = query.filter(Channel.is_active == True)
        
        channels = query.all()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        channel_summaries = []
        for channel in channels:
            summary = get_sentiment_summary(channel.id, start_date, end_date, db)
            channel_summaries.append({
                "channel": {
                    "id": channel.id,
                    "name": channel.name
                },
                "summary": summary
            })
        
        # Calculate overall statistics
        total_messages = sum(cs["summary"]["message_count"] for cs in channel_summaries)
        avg_sentiment = sum(cs["summary"]["average_sentiment"] * cs["summary"]["message_count"] 
                           for cs in channel_summaries if cs["summary"]["message_count"] > 0) / max(total_messages, 1)
        
        return {
            "period_days": days,
            "total_channels": len(channels),
            "total_messages": total_messages,
            "overall_sentiment": round(avg_sentiment, 3),
            "channels": channel_summaries
        }
        
    except Exception as e:
        logger.error(f"Error getting all sentiment data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Insights endpoints
@router.get("/insights")
async def get_insights(
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of insights"),
    db: Session = Depends(get_db)
):
    """Get actionable insights"""
    try:
        query = db.query(Insight).filter(Insight.is_active == True)
        
        if channel_id:
            query = query.filter(Insight.channel_id == channel_id)
        if severity:
            query = query.filter(Insight.severity == severity)
        
        insights = query.order_by(
            Insight.created_at.desc()
        ).limit(limit).all()
        
        return {
            "insights": [
                {
                    "id": insight.id,
                    "channel_id": insight.channel_id,
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "severity": insight.severity,
                    "recommendation": insight.recommendation,
                    "created_at": insight.created_at.isoformat(),
                    "acknowledged": insight.acknowledged_by is not None,
                    "data_source": insight.data_source
                }
                for insight in insights
            ],
            "count": len(insights),
            "filters": {
                "channel_id": channel_id,
                "severity": severity
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights/{insight_id}/acknowledge")
async def acknowledge_insight_endpoint(
    insight_id: int,
    acknowledge_data: InsightAcknowledge,
    db: Session = Depends(get_db)
):
    """Acknowledge an insight"""
    try:
        success = acknowledge_insight(insight_id, acknowledge_data.acknowledged_by, db)
        
        if not success:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        return {"message": "Insight acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights/generate")
async def generate_insights_endpoint(
    channel_id: Optional[str] = Query(None, description="Generate for specific channel"),
    db: Session = Depends(get_db)
):
    """Manually trigger insight generation"""
    try:
        if channel_id:
            # Generate for specific channel
            insights = generate_engagement_insights(channel_id, db)
            for insight in insights:
                db.add(insight)
            db.commit()
            
            return {
                "message": f"Generated {len(insights)} insights for channel {channel_id}",
                "insights_count": len(insights)
            }
        else:
            # Generate for all channels
            run_insight_generation_job()
            return {"message": "Insight generation job triggered for all channels"}
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{channel_id}")
async def get_channel_recommendations_endpoint(
    channel_id: str,
    db: Session = Depends(get_db)
):
    """Get actionable recommendations for a channel"""
    try:
        recommendations = generate_channel_recommendations(channel_id, db)
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard and summary endpoints
@router.get("/dashboard")
async def get_dashboard_data(
    days: int = Query(30, ge=1, le=90, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data"""
    try:
        # Get active channels
        channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        # Get recent insights
        recent_insights = db.query(Insight).filter(
            Insight.is_active == True,
            Insight.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(Insight.severity.desc()).limit(10).all()
        
        # Get weekly summaries for all channels
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        weekly_summaries = db.query(WeeklySummary).filter(
            WeeklySummary.week_start >= start_date
        ).all()
        
        # Calculate dashboard metrics
        total_messages = sum(ws.message_count for ws in weekly_summaries)
        avg_sentiment = sum(ws.avg_sentiment * ws.message_count for ws in weekly_summaries) / max(total_messages, 1)
        burnout_alerts = sum(1 for ws in weekly_summaries if ws.burnout_flag)
        
        # Engagement level distribution
        engagement_levels = {}
        for ws in weekly_summaries:
            level = ws.engagement_level
            engagement_levels[level] = engagement_levels.get(level, 0) + 1
        
        return {
            "period_days": days,
            "overview": {
                "total_channels": len(channels),
                "active_channels": len([c for c in channels if c.is_active]),
                "total_messages": total_messages,
                "average_sentiment": round(avg_sentiment, 3),
                "burnout_alerts": burnout_alerts,
                "recent_insights": len(recent_insights)
            },
            "engagement_distribution": engagement_levels,
            "recent_insights": [
                {
                    "id": insight.id,
                    "channel_id": insight.channel_id,
                    "title": insight.title,
                    "severity": insight.severity,
                    "created_at": insight.created_at.isoformat()
                }
                for insight in recent_insights
            ],
            "sentiment_trend": "improving" if avg_sentiment > 0.1 else "declining" if avg_sentiment < -0.1 else "stable"
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team-metrics")
async def get_team_metrics(
    channels: str = Query("", description="Comma-separated list of channel names"),
    days: int = Query(7, ge=1, le=90, description="Period in days"),
    db: Session = Depends(get_db)
):
    """Get team metrics data for the dashboard"""
    try:
        # Parse channels parameter
        selected_channels = []
        if channels:
            channel_names = [c.strip() for c in channels.split(',') if c.strip()]
            if channel_names:
                selected_channels = db.query(Channel).filter(
                    Channel.name.in_(channel_names),
                    Channel.is_active == True
                ).all()
        else:
            selected_channels = db.query(Channel).filter(Channel.is_active == True).all()
        
        # Get sentiment data for selected channels
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        total_messages = 0
        avg_sentiment = 0.0
        channel_sentiments = []
        
        for channel in selected_channels:
            summary = get_sentiment_summary(channel.id, start_date, end_date, db)
            total_messages += summary["message_count"]
            if summary["message_count"] > 0:
                channel_sentiments.append(summary["average_sentiment"])
        
        if channel_sentiments:
            avg_sentiment = sum(channel_sentiments) / len(channel_sentiments)
        
        # Calculate overall health (0-10 scale)
        overall_health = max(0, min(10, 5 + (avg_sentiment * 10)))
        
        # Determine sentiment label
        if avg_sentiment > 0.1:
            sentiment_label = "Positive"
        elif avg_sentiment < -0.1:
            sentiment_label = "Negative" 
        else:
            sentiment_label = "Neutral"
        
        # Determine burnout risk
        if avg_sentiment < -0.3:
            burnout_risk = "High"
        elif avg_sentiment < -0.1:
            burnout_risk = "Medium"
        else:
            burnout_risk = "Low"
        
        # Get recent insights
        recent_insights = db.query(Insight).filter(
            Insight.is_active == True,
            Insight.created_at >= datetime.now() - timedelta(days=7)
        ).order_by(Insight.severity.desc()).limit(5).all()
        
        insights_data = []
        for insight in recent_insights:
            insights_data.append({
                "title": insight.title,
                "description": insight.description,
                "priority": insight.severity,
                "category": insight.insight_type
            })
        
        # Generate action items based on data
        action_items = []
        if avg_sentiment < -0.2:
            action_items.append({
                "title": "Address Team Sentiment",
                "description": f"Average sentiment is {avg_sentiment:.2f}. Consider team check-ins.",
                "priority": "high",
                "category": "wellbeing"
            })
        
        if total_messages < 5:
            action_items.append({
                "title": "Encourage Team Communication", 
                "description": f"Only {total_messages} messages in {days} days. Consider team engagement activities.",
                "priority": "medium",
                "category": "engagement"
            })
        
        # Build team breakdown (channels with their scores)
        team_breakdown = {}
        for channel in selected_channels:
            summary = get_sentiment_summary(channel.id, start_date, end_date, db)
            if summary["message_count"] > 0:
                # Convert sentiment to score (0-10 scale)
                channel_health = max(0, min(10, 5 + (summary["average_sentiment"] * 10)))
                team_breakdown[channel.name] = round(channel_health, 1)
            else:
                team_breakdown[channel.name] = 5.0  # Neutral score for no messages
        
        return {
            "overall_health": round(overall_health, 1),
            "sentiment": sentiment_label,
            "sentiment_score": sentiment_label,  # Dashboard expects this field name
            "burnout_risk": burnout_risk,
            "message_count": total_messages,
            "insights": insights_data,
            "action_items": action_items,
            "team_breakdown": team_breakdown,
            "selected_channels": [ch.name for ch in selected_channels],
            "last_updated": datetime.now().isoformat(),
            "daily_summary": {
                "total_messages": total_messages,
                "avg_sentiment": round(avg_sentiment, 3),
                "active_channels": len(selected_channels)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting team metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# System and admin endpoints
@router.get("/system/status")
async def get_system_status():
    """Get system status including scheduler and jobs"""
    try:
        scheduler_status = get_scheduler_status()
        
        return {
            "system": "operational",
            "timestamp": datetime.now().isoformat(),
            "scheduler": scheduler_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/jobs/{job_id}/trigger")
async def trigger_job(job_id: str):
    """Manually trigger a scheduled job"""
    try:
        valid_jobs = ["daily_aggregation", "weekly_aggregation"]
        if job_id not in valid_jobs:
            raise HTTPException(status_code=400, detail=f"Invalid job ID. Valid jobs: {valid_jobs}")
        
        result = trigger_job_manually(job_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/backfill")
async def backfill_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    channel_ids: Optional[List[str]] = Query(None, description="Specific channel IDs to backfill")
):
    """Backfill historical data summaries"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # Run backfill
        backfill_summaries(start, end, channel_ids)
        
        return {
            "message": "Backfill completed successfully",
            "start_date": start_date,
            "end_date": end_date,
            "channels": channel_ids or "all active channels"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error in backfill: {e}")
        raise HTTPException(status_code=500, detail=str(e))
