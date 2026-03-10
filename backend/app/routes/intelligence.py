from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.models.intelligence import IntelligenceCard
from app.utils.cache import cached

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

class IntelligenceCardSchema(BaseModel):
    id: int
    topic_id: int
    category: str
    icon: str
    title: str
    description: str
    trend_percentage: str
    is_positive: bool
    display_order: int
    
    class Config:
        from_attributes = True

@router.get("/cards", response_model=List[IntelligenceCardSchema])
@cached(ttl=300, prefix="intelligence_cards")
async def get_intelligence_cards(
    limit: int = 6,
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get intelligence cards for homepage display."""
    query = select(IntelligenceCard).order_by(IntelligenceCard.display_order.desc())
    
    if category:
        query = query.where(IntelligenceCard.category == category)
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    cards = result.scalars().all()
    
    return cards
