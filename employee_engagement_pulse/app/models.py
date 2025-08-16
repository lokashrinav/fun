"""
SQLAlchemy models for Employee Engagement Pulse
"""
import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./employee_pulse.db")
engine = create_engine(DATABASE_URL, echo=os.getenv("DEBUG", "False").lower() == "true")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Channel(Base):
    """Monitored Slack channels"""
    __tablename__ = "channels"
    
    id = Column(String, primary_key=True)  # Slack channel ID
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    raw_events = relationship("RawEvent", back_populates="channel_obj")
    sentiments = relationship("Sentiment", back_populates="channel_obj")


class RawEvent(Base):
    """Raw Slack events from the API"""
    __tablename__ = "raw_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)  # message, reaction_added, etc.
    channel_id = Column(String, ForeignKey("channels.id"))
    user_id = Column(String)
    timestamp = Column(String)  # Slack timestamp format
    json_data = Column(JSON, nullable=False)  # Full event payload
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    channel_obj = relationship("Channel", back_populates="raw_events")


class Sentiment(Base):
    """Sentiment analysis results for individual messages"""
    __tablename__ = "sentiments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    user_id = Column(String)
    message_ts = Column(String)  # Slack timestamp
    text_content = Column(Text)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    confidence = Column(Float)
    emoji_boost = Column(Float, default=0.0)
    reaction_boost = Column(Float, default=0.0)
    final_score = Column(Float, nullable=False)
    analysis_date = Column(Date, default=func.current_date())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    channel_obj = relationship("Channel", back_populates="sentiments")


class DailySummary(Base):
    """Daily aggregated sentiment data per channel"""
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    summary_date = Column(Date, nullable=False)
    message_count = Column(Integer, default=0)
    avg_sentiment = Column(Float)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    most_active_users = Column(JSON)  # Top 5 users by message count
    peak_activity_hour = Column(Integer)  # Hour with most messages
    created_at = Column(DateTime, default=func.now())
    
    # Add unique constraint on channel_id and summary_date
    __table_args__ = (
        {'extend_existing': True}
    )


class WeeklySummary(Base):
    """Weekly aggregated sentiment data per channel"""
    __tablename__ = "weekly_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    week_start = Column(Date, nullable=False)  # Monday of the week
    week_end = Column(Date, nullable=False)    # Sunday of the week
    message_count = Column(Integer, default=0)
    avg_sentiment = Column(Float)
    sentiment_trend = Column(Float)  # Change from previous week
    burnout_flag = Column(Boolean, default=False)
    engagement_level = Column(String)  # High, Medium, Low, Critical
    top_topics = Column(JSON)  # Most discussed topics/keywords
    active_user_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class Insight(Base):
    """Generated insights and recommendations"""
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"))
    insight_type = Column(String, nullable=False)  # burnout_alert, engagement_spike, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    actionable = Column(Boolean, default=True)
    recommendation = Column(Text)
    data_source = Column(JSON)  # Supporting data for the insight
    is_active = Column(Boolean, default=True)
    acknowledged_by = Column(String)  # User who acknowledged the insight
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())


class User(Base):
    """Slack user information (cached from API)"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Slack user ID
    real_name = Column(String)
    display_name = Column(String)
    email = Column(String)
    is_admin = Column(Boolean, default=False)
    is_bot = Column(Boolean, default=False)
    timezone = Column(String)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
