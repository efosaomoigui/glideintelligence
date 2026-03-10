import enum
from sqlalchemy import String, Boolean, ForeignKey, Integer, TIMESTAMP, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional
from datetime import datetime

from app.models.base import Base, TimestampMixin

class SourceType(str, enum.Enum):
    RSS = "rss"
    API = "api"
    WEBSITE = "website"
    SOCIAL = "social"

class SourceCategory(str, enum.Enum):
    GENERAL = "general"
    GOVERNMENT = "government"
    FINANCIAL = "financial"
    SOCIAL = "social"

class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType, values_callable=lambda obj: [e.value for e in obj]), default=SourceType.WEBSITE, server_default="website")
    category: Mapped[SourceCategory] = mapped_column(Enum(SourceCategory, values_callable=lambda obj: [e.value for e in obj]), default=SourceCategory.GENERAL, server_default="general")
    url: Mapped[str] = mapped_column(String)
    domain: Mapped[str] = mapped_column(String, unique=True, index=True)
    api_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reliability_score: Mapped[float] = mapped_column(default=0.0)
    bias_rating: Mapped[float] = mapped_column(default=0.0)  # -1.0 (left) to 1.0 (right)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Enhanced Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True) # metadata is reserved in SQLAlchemy
    fetch_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    fetch_error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    articles: Mapped[List["RawArticle"]] = relationship("RawArticle", back_populates="source", cascade="all, delete-orphan")
    health: Mapped[Optional["SourceHealth"]] = relationship("SourceHealth", back_populates="source", uselist=False, cascade="all, delete-orphan")
    group_memberships: Mapped[List["SourceGroupMember"]] = relationship("SourceGroupMember", back_populates="source", cascade="all, delete-orphan")

class SourceHealth(Base, TimestampMixin):
    __tablename__ = "source_health"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), unique=True)
    status: Mapped[str] = mapped_column(String, default="healthy") # healthy, degraded, down
    last_success: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped["Source"] = relationship("Source", back_populates="health")
