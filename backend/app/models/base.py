from datetime import datetime
from typing import Any
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
