from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, INET
from typing import List, Optional
from datetime import datetime

from app.models.base import Base, TimestampMixin

class Vertical(Base, TimestampMixin):
    __tablename__ = "verticals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    tag_type: Mapped[str] = mapped_column(String, default="keyword") # topic, entity, location, keyword
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    topics: Mapped[List["TopicTag"]] = relationship("TopicTag", back_populates="tag", cascade="all, delete-orphan")

class TopicTag(Base, TimestampMixin):
    __tablename__ = "topic_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), index=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="topics")

class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    email_digest_frequency: Mapped[str] = mapped_column(String, default="daily") # daily, weekly, never
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    preferred_categories: Mapped[Optional[List[int]]] = mapped_column(JSONB, nullable=True) # List of vertical IDs
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    user: Mapped["User"] = relationship("User", back_populates="preferences")

class AnalyticsEvent(Base, TimestampMixin):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True) # topic_view, article_click
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
