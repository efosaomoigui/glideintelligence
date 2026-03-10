from sqlalchemy import String, Integer, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional

from app.models.base import Base, TimestampMixin

class ImpactCategory(Base, TimestampMixin):
    __tablename__ = "impact_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True) # "Economic", "Social"
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True) # emoji or icon name
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    impacts: Mapped[List["RegionalImpact"]] = relationship("RegionalImpact", back_populates="category", cascade="all, delete-orphan")

class RegionalImpact(Base, TimestampMixin):
    __tablename__ = "regional_impacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    impact_category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("impact_categories.id"), index=True, nullable=True) # Optional now as we might use string category
    impact_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Direct string support from reference
    
    icon: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    title: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # low, medium, high, critical
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Kept for backward compat if needed
    is_current: Mapped[bool] = mapped_column(default=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="regional_impacts")
    category: Mapped["ImpactCategory"] = relationship("ImpactCategory", back_populates="impacts")
    details: Mapped[List["ImpactDetail"]] = relationship("ImpactDetail", back_populates="impact", cascade="all, delete-orphan")

class ImpactDetail(Base, TimestampMixin):
    __tablename__ = "impact_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    regional_impact_id: Mapped[int] = mapped_column(ForeignKey("regional_impacts.id"), index=True)
    label: Mapped[str] = mapped_column(String) # "Immediate Effect"
    value: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    impact: Mapped["RegionalImpact"] = relationship("RegionalImpact", back_populates="details")

class ImpactMetric(Base, TimestampMixin):
    __tablename__ = "impact_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    metric_type: Mapped[str] = mapped_column(String) # "currency_impact"
    metric_value: Mapped[float] = mapped_column(Float)
    metric_unit: Mapped[str] = mapped_column(String) # "NGN", "%"
    time_frame: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
