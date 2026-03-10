from sqlalchemy import String, Integer, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional

from app.models.base import Base, TimestampMixin

class SourceGroup(Base, TimestampMixin):
    __tablename__ = "source_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True) # "Nigerian Media", "Business Press"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    members: Mapped[List["SourceGroupMember"]] = relationship("SourceGroupMember", back_populates="group", cascade="all, delete-orphan")
    perspectives: Mapped[List["TopicPerspective"]] = relationship("TopicPerspective", back_populates="group", cascade="all, delete-orphan")

class SourceGroupMember(Base, TimestampMixin):
    __tablename__ = "source_group_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    source_group_id: Mapped[int] = mapped_column(ForeignKey("source_groups.id"), index=True)
    
    source: Mapped["Source"] = relationship("Source", back_populates="group_memberships")
    group: Mapped["SourceGroup"] = relationship("SourceGroup", back_populates="members")

class TopicPerspective(Base, TimestampMixin):
    __tablename__ = "topic_perspectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    source_group_id: Mapped[int] = mapped_column(ForeignKey("source_groups.id"), index=True)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0) # -100 to 100
    sentiment_label: Mapped[str] = mapped_column(String, default="neutral") # positive, negative, neutral, mixed
    stance_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_emphasis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="perspectives")
    group: Mapped["SourceGroup"] = relationship("SourceGroup", back_populates="perspectives")
    quotes: Mapped[List["PerspectiveQuote"]] = relationship("PerspectiveQuote", back_populates="perspective", cascade="all, delete-orphan")

class PerspectiveQuote(Base, TimestampMixin):
    __tablename__ = "perspective_quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_perspective_id: Mapped[int] = mapped_column(ForeignKey("topic_perspectives.id"), index=True)
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_articles.id"), nullable=True)
    quote_text: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_featured: Mapped[bool] = mapped_column(default=False)
    
    perspective: Mapped["TopicPerspective"] = relationship("TopicPerspective", back_populates="quotes")

class SentimentAnalysis(Base, TimestampMixin):
    __tablename__ = "sentiment_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id"), index=True)
    overall_sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_label: Mapped[str] = mapped_column(String, default="neutral")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    emotional_tone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    key_phrases: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    entities_mentioned: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    analyzed_by: Mapped[str] = mapped_column(String, default="ai")
