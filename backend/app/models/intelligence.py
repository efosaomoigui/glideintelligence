from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List, Dict
from datetime import datetime

from app.models.base import Base, TimestampMixin

class CategoryConfig(Base, TimestampMixin):
    """Configuration for category-specific AI analysis dimensions."""
    __tablename__ = "category_configs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    dimension_mappings: Mapped[dict] = mapped_column(JSONB)
    impact_categories: Mapped[list] = mapped_column(JSONB)

class SourcePerspective(Base, TimestampMixin):
    """How different sources frame the same story."""
    __tablename__ = "source_perspectives"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    source_name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    frame_label: Mapped[str] = mapped_column(String(100))
    sentiment: Mapped[str] = mapped_column(String(20))
    sentiment_percentage: Mapped[str] = mapped_column(String(10))
    key_narrative: Mapped[str] = mapped_column(Text)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="source_perspectives")

class IntelligenceCard(Base, TimestampMixin):
    """Concise intelligence cards for homepage display."""
    __tablename__ = "intelligence_cards"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50))
    icon: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(200))
    trend_percentage: Mapped[str] = mapped_column(String(10))
    is_positive: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="intelligence_card")
