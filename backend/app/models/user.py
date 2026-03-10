from sqlalchemy import String, Boolean, Text, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Optional for social login
    raw_password: Mapped[Optional[str]] = mapped_column(String, nullable=True) # TEMPORARY: For auto-generated magic-login passwords
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Auth Provider
    auth_provider: Mapped[str] = mapped_column(String, default="email") # email, google, apple
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True, index=True)
    
    # Profile
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Status & Role
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user") # user, expert, moderator, admin
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    verification_expires: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    verification_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reputation_score: Mapped[int] = mapped_column(Integer, default=0)
    
    last_active_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user")
    poll_votes: Mapped[List["PollVote"]] = relationship("PollVote", back_populates="user")
    preferences: Mapped[Optional["UserPreference"]] = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

