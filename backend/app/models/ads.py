import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
import enum

class AdType(str, enum.Enum):
    EXTERNAL = "external"
    SPONSOR = "sponsor"
    IMAGE = "image"

class AdStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Ad(Base):
    __tablename__ = "ads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_type = Column(SQLEnum(AdType), nullable=False)
    title = Column(String, nullable=False)
    status = Column(SQLEnum(AdStatus), default=AdStatus.ACTIVE, nullable=False)
    placement_group = Column(String, nullable=False, index=True)
    priority = Column(Integer, default=0)
    
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    cpm_value = Column(Numeric(10, 2), default=0.0)
    cpc_value = Column(Numeric(10, 2), default=0.0)
    
    views_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    revenue_generated = Column(Numeric(12, 2), default=0.0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships mapped to subclass details
    external = relationship("AdExternalNetwork", back_populates="ad", uselist=False, cascade="all, delete-orphan")
    sponsor = relationship("AdSponsor", back_populates="ad", uselist=False, cascade="all, delete-orphan")
    image = relationship("AdImage", back_populates="ad", uselist=False, cascade="all, delete-orphan")
    events = relationship("AdEvent", back_populates="ad", cascade="all, delete-orphan")


class AdExternalNetwork(Base):
    __tablename__ = "ad_external_network"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_id = Column(String(36), ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, unique=True)
    network_name = Column(String, nullable=False)
    ad_size = Column(String, nullable=True)
    script_code = Column(Text, nullable=False)
    is_rotating = Column(Boolean, default=True)
    display_on_homepage = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ad = relationship("Ad", back_populates="external")


class AdSponsor(Base):
    __tablename__ = "ad_sponsor"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_id = Column(String(36), ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, unique=True)
    tagline = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    website_link = Column(String, nullable=True)
    cta_text = Column(String, default="Learn More")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ad = relationship("Ad", back_populates="sponsor")


class AdImage(Base):
    __tablename__ = "ad_image"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_id = Column(String(36), ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, unique=True)
    image_url = Column(String, nullable=False)
    target_url = Column(String, nullable=False)
    alt_text = Column(String, nullable=True)
    ad_size = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ad = relationship("Ad", back_populates="image")


class EventType(str, enum.Enum):
    VIEW = "view"
    CLICK = "click"

class AdEvent(Base):
    __tablename__ = "ad_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_id = Column(String(36), ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(SQLEnum(EventType), nullable=False)
    page_location = Column(String, nullable=True)
    user_session = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    ad = relationship("Ad", back_populates="events")
