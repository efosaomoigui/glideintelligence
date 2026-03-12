from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base import Base, TimestampMixin

class TopicRegionalCategory(Base, TimestampMixin):
    __tablename__ = "topic_regional_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    region_name: Mapped[str] = mapped_column(String(100), index=True)
    impact: Mapped[str] = mapped_column(String(50), default="Neutral") # Positive, Negative, Neutral

    topic: Mapped["Topic"] = relationship("Topic", back_populates="regional_categories")
