from sqlalchemy import String, Integer, ForeignKey, Text, Float, Index, JSON, Boolean, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from typing import List, Optional
from datetime import datetime

from app.models.base import Base, TimestampMixin

class RawArticle(Base, TimestampMixin):
    __tablename__ = "raw_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(String, index=True) # ID from the external source
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    published_at: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Keep as string for now to match raw data? Or better datetime.
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Extended Content Fields
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Deduplication
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_articles.id"), nullable=True)
    
    # Analysis fields
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="articles")
    entities: Mapped[List["ArticleEntity"]] = relationship("ArticleEntity", back_populates="article", cascade="all, delete-orphan")
    embedding: Mapped[Optional["ArticleEmbedding"]] = relationship("ArticleEmbedding", back_populates="article", uselist=False, cascade="all, delete-orphan")
    
    # Topic relationships
    topic_associations: Mapped[List["TopicArticle"]] = relationship("TopicArticle", back_populates="article", cascade="all, delete-orphan")
    
    # Self-referential relationship for duplicates
    original_article: Mapped[Optional["RawArticle"]] = relationship("RawArticle", remote_side=[id], backref="duplicates")
    
    # YouTube extension
    youtube_video: Mapped[Optional["YouTubeVideo"]] = relationship("YouTubeVideo", back_populates="article", uselist=False, cascade="all, delete-orphan")


class YouTubeVideo(Base, TimestampMixin):
    __tablename__ = "youtube_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id"), unique=True)
    video_id: Mapped[str] = mapped_column(String(50), index=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    embed_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    article: Mapped["RawArticle"] = relationship("RawArticle", back_populates="youtube_video")


class CollectionJob(Base, TimestampMixin):
    __tablename__ = "collection_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    job_type: Mapped[str] = mapped_column(String, default="scheduled") # scheduled, manual, backfill
    status: Mapped[str] = mapped_column(String, default="pending") # pending, running, completed, failed
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, default=0)
    articles_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class ArticleEntity(Base, TimestampMixin):
    __tablename__ = "article_entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id"), index=True)
    entity_name: Mapped[str] = mapped_column(String, index=True)
    entity_type: Mapped[str] = mapped_column(String, index=True) # e.g., PERSON, LOC, ORG
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    
    article: Mapped["RawArticle"] = relationship("RawArticle", back_populates="entities")

class ArticleEmbedding(Base, TimestampMixin):
    __tablename__ = "article_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id", ondelete="CASCADE"), unique=True, index=True)
    
    # Using pgvector. Dimension size is 384 for all-MiniLM-L6-v2.
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))
    
    article: Mapped["RawArticle"] = relationship("RawArticle", back_populates="embedding")
