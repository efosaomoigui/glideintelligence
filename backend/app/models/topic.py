from sqlalchemy import String, Integer, ForeignKey, Text, Float, Boolean, JSON, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict
from datetime import datetime

from app.models.base import Base, TimestampMixin

class Topic(Base, TimestampMixin):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String, index=True)
    subcategories: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, default="developing", index=True) # developing, stable, resolved, archived
    analysis_status: Mapped[str] = mapped_column(String, default="pending", index=True) # pending, processing, complete, failed, verified
    importance_score: Mapped[float] = mapped_column(Float, default=0.0, index=True) # 0.00 to 1.00
    
    # Sentiment
    overall_sentiment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Display Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    engagement_count: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    featured_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Advanced Metadata
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    coverage_level: Mapped[str] = mapped_column(String, default="low") # low, medium, high
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    
    # Relationships
    article_associations: Mapped[List["TopicArticle"]] = relationship("TopicArticle", back_populates="topic", cascade="all, delete-orphan")
    analysis: Mapped[Optional["TopicAnalysis"]] = relationship("TopicAnalysis", back_populates="topic", uselist=False, cascade="all, delete-orphan")
    ai_summaries: Mapped[List["AISummary"]] = relationship("AISummary", back_populates="topic", cascade="all, delete-orphan")
    perspectives: Mapped[List["TopicPerspective"]] = relationship("TopicPerspective", back_populates="topic", cascade="all, delete-orphan")
    regional_impacts: Mapped[List["RegionalImpact"]] = relationship("RegionalImpact", back_populates="topic", cascade="all, delete-orphan")
    regional_categories: Mapped[List["TopicRegionalCategory"]] = relationship("TopicRegionalCategory", back_populates="topic", cascade="all, delete-orphan")
    sentiment_breakdown: Mapped[List["TopicSentimentBreakdown"]] = relationship("TopicSentimentBreakdown", back_populates="topic", cascade="all, delete-orphan")
    source_perspectives: Mapped[List["SourcePerspective"]] = relationship("SourcePerspective", back_populates="topic", cascade="all, delete-orphan")
    intelligence_card: Mapped[Optional["IntelligenceCard"]] = relationship("IntelligenceCard", back_populates="topic", uselist=False, cascade="all, delete-orphan")
    trends: Mapped[List["TopicTrend"]] = relationship("TopicTrend", back_populates="topic", cascade="all, delete-orphan")
    videos: Mapped[List["TopicVideo"]] = relationship("TopicVideo", back_populates="topic", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="topic", cascade="all, delete-orphan")
    polls: Mapped[List["Poll"]] = relationship("Poll", back_populates="topic", cascade="all, delete-orphan")
    tags: Mapped[List["TopicTag"]] = relationship("TopicTag", back_populates="topic", cascade="all, delete-orphan")


class TopicArticle(Base, TimestampMixin):
    __tablename__ = "topic_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id"), index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_by: Mapped[str] = mapped_column(String, default="ai") # ai, manual, hybrid
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="article_associations")
    article: Mapped["RawArticle"] = relationship("RawArticle", back_populates="topic_associations")


class TopicAnalysis(Base, TimestampMixin):
    __tablename__ = "topic_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text)
    facts: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    regional_framing: Mapped[Optional[Dict[str, str]]] = mapped_column(JSONB, nullable=True)
    
    # Intelligence Agent Fields
    executive_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    what_you_need_to_know: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    key_takeaways: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    drivers_of_story: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    strategic_implications: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    regional_impact: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Enrichment Fallbacks
    sentiment_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    framing_overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="analysis")

class TopicSentimentBreakdown(Base, TimestampMixin):
    """Dimension-based sentiment analysis for topics."""
    __tablename__ = "topic_sentiment_breakdown"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    dimension_type: Mapped[str] = mapped_column(String(50))
    dimension_value: Mapped[str] = mapped_column(String(100))
    sentiment: Mapped[str] = mapped_column(String(20))
    sentiment_score: Mapped[float] = mapped_column(Float)
    percentage: Mapped[float] = mapped_column(Float)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="sentiment_breakdown")


class AISummary(Base, TimestampMixin):
    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    summary_type: Mapped[str] = mapped_column(String, default="60_second") # 60_second, deep_dive, daily_digest
    content: Mapped[str] = mapped_column(Text)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bullet_points: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    key_takeaway: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), default=datetime.now)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="ai_summaries")


class SummaryUpdate(Base, TimestampMixin):
    __tablename__ = "summary_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    old_summary_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_summaries.id"), nullable=True)
    new_summary_id: Mapped[int] = mapped_column(ForeignKey("ai_summaries.id"))
    trigger_reason: Mapped[str] = mapped_column(String, default="new_article")
    articles_added_count: Mapped[int] = mapped_column(Integer, default=0)
    content_diff_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class TopicTrend(Base, TimestampMixin):
    __tablename__ = "topic_trends"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True)
    interest_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="trends")

class TopicVideo(Base, TimestampMixin):
    __tablename__ = "topic_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    video_url: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_platform: Mapped[str] = mapped_column(String, default="youtube") # youtube, vimeo, etc.
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="videos")
