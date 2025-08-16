"""
APScheduler configuration for running aggregation jobs
"""
import os
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from app.aggregator import run_daily_aggregation_job, run_weekly_aggregation_job

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: BackgroundScheduler = None


def job_listener(event):
    """Listen to job execution events"""
    if event.exception:
        logger.error(f"Job {event.job_id} crashed: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler is already running")
        return
    
    try:
        scheduler = BackgroundScheduler()
        
        # Add job listener
        scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Configure daily aggregation job
        daily_hour = int(os.getenv("DAILY_JOB_HOUR", 1))  # Default: 1 AM
        scheduler.add_job(
            run_daily_aggregation_job,
            trigger=CronTrigger(hour=daily_hour, minute=0),
            id="daily_aggregation",
            name="Daily Sentiment Aggregation",
            replace_existing=True,
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        # Configure weekly aggregation job (runs on Mondays)
        weekly_day = int(os.getenv("WEEKLY_JOB_DAY", 0))  # Default: Monday
        weekly_hour = int(os.getenv("WEEKLY_JOB_HOUR", 2))  # Default: 2 AM
        scheduler.add_job(
            run_weekly_aggregation_job,
            trigger=CronTrigger(day_of_week=weekly_day, hour=weekly_hour, minute=0),
            id="weekly_aggregation",
            name="Weekly Sentiment Aggregation",
            replace_existing=True,
            misfire_grace_time=7200  # 2 hour grace period
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Background scheduler started successfully")
        logger.info(f"Daily job scheduled at {daily_hour:02d}:00")
        logger.info(f"Weekly job scheduled on day {weekly_day} at {weekly_hour:02d}:00")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler is not running")
        return
    
    try:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("Background scheduler stopped successfully")
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


def get_scheduler_status():
    """Get current scheduler status and job information"""
    global scheduler
    
    if scheduler is None:
        return {
            "status": "stopped",
            "jobs": []
        }
    
    try:
        jobs = []
        for job in scheduler.get_jobs():
            # Get next run time
            next_run = job.next_run_time
            next_run_str = next_run.isoformat() if next_run else "No scheduled runs"
            
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run_str,
                "trigger": str(job.trigger),
                "func_name": job.func.__name__ if job.func else "Unknown"
            })
        
        return {
            "status": "running" if scheduler.running else "paused",
            "job_count": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "jobs": []
        }


def trigger_job_manually(job_id: str):
    """Manually trigger a scheduled job"""
    global scheduler
    
    if scheduler is None:
        raise ValueError("Scheduler is not running")
    
    try:
        job = scheduler.get_job(job_id)
        if job is None:
            raise ValueError(f"Job '{job_id}' not found")
        
        # Run the job now
        scheduler.modify_job(job_id, next_run_time=datetime.now())
        logger.info(f"Manually triggered job: {job_id}")
        
        return {"success": True, "message": f"Job {job_id} triggered successfully"}
        
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        return {"success": False, "error": str(e)}


def add_custom_job(func, trigger, job_id: str, name: str = None, **kwargs):
    """Add a custom job to the scheduler"""
    global scheduler
    
    if scheduler is None:
        raise ValueError("Scheduler is not running")
    
    try:
        scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            replace_existing=True,
            **kwargs
        )
        
        logger.info(f"Added custom job: {job_id}")
        return {"success": True, "message": f"Job {job_id} added successfully"}
        
    except Exception as e:
        logger.error(f"Error adding custom job {job_id}: {e}")
        return {"success": False, "error": str(e)}


def remove_job(job_id: str):
    """Remove a job from the scheduler"""
    global scheduler
    
    if scheduler is None:
        raise ValueError("Scheduler is not running")
    
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed job: {job_id}")
        return {"success": True, "message": f"Job {job_id} removed successfully"}
        
    except Exception as e:
        logger.error(f"Error removing job {job_id}: {e}")
        return {"success": False, "error": str(e)}
