from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, JSON, Float, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from app.models.base import Base, TimestampMixin

class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topics.id"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"), nullable=True)
    
    # Engagement & Moderation
    upvote_count: Mapped[int] = mapped_column(Integer, default=0)
    downvote_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_status: Mapped[str] = mapped_column(String, default="pending") # pending, approved, flagged, removed
    
    user: Mapped["User"] = relationship("User", back_populates="comments")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="comments")
    replies: Mapped[List["Comment"]] = relationship("Comment", remote_side=[id])
    votes: Mapped[List["CommentVote"]] = relationship("CommentVote", back_populates="comment", cascade="all, delete-orphan")
    insight: Mapped[Optional["CommunityInsight"]] = relationship("CommunityInsight", back_populates="comment", uselist=False, cascade="all, delete-orphan")

class CommentVote(Base, TimestampMixin):
    __tablename__ = "comment_votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vote_type: Mapped[str] = mapped_column(String) # upvote, downvote
    
    comment: Mapped["Comment"] = relationship("Comment", back_populates="votes")
    user: Mapped["User"] = relationship("User") # No back_populate needed strictly, or add to User

class Poll(Base, TimestampMixin):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topics.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(String)
    poll_type: Mapped[str] = mapped_column(String, default="single_choice") # single_choice, multiple_choice, ranking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_backed_up: Mapped[bool] = mapped_column(Boolean, default=False)
    closes_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    total_votes: Mapped[int] = mapped_column(Integer, default=0)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    topic: Mapped["Topic"] = relationship("Topic", back_populates="polls")
    options: Mapped[List["PollOption"]] = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes: Mapped[List["PollVote"]] = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")

class PollOption(Base, TimestampMixin):
    __tablename__ = "poll_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id"), index=True)
    option_text: Mapped[str] = mapped_column(String)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    
    poll: Mapped["Poll"] = relationship("Poll", back_populates="options")

class PollVote(Base, TimestampMixin):
    __tablename__ = "poll_votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id"), index=True)
    poll_option_id: Mapped[int] = mapped_column(ForeignKey("poll_options.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ranking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    poll: Mapped["Poll"] = relationship("Poll", back_populates="votes")
    user: Mapped["User"] = relationship("User", back_populates="poll_votes")

class CommunityInsight(Base, TimestampMixin):
    __tablename__ = "community_insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), unique=True)
    insight_type: Mapped[str] = mapped_column(String) # expert_perspective, local_knowledge
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    identified_by: Mapped[str] = mapped_column(String, default="ai")
    display_location: Mapped[str] = mapped_column(String, default="sidebar")
    
    comment: Mapped["Comment"] = relationship("Comment", back_populates="insight")
