from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.models.base import Base, TimestampMixin

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String) # e.g., "TOGGLE_FEATURE_FLAG", "UPDATE_AI_PROVIDER"
    target: Mapped[str] = mapped_column(String) # e.g., "FEATURE_FLAG:CRAWLER"
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON string or description
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    user: Mapped["User"] = relationship("User")
