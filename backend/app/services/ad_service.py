from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from datetime import datetime
from uuid import UUID

from app.models.ads import Ad, AdStatus, AdEvent, EventType, AdExternalNetwork, AdSponsor, AdImage

class AdService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ad_for_placement(self, placement_group: str, limit: int = 1) -> list[Ad]:
        """
        Fetch random active ads for a specific placement group, respecting dates.
        """
        now = datetime.utcnow()
        from sqlalchemy.orm import selectinload
        
        # Build query for active ads in this placement group
        # that are within their date bounds
        query = (
            select(Ad)
            .options(
                selectinload(Ad.external),
                selectinload(Ad.sponsor),
                selectinload(Ad.image)
            )
            .where(Ad.status == AdStatus.ACTIVE)
            .where(Ad.placement_group == placement_group)
            .where(
                and_(
                    (Ad.start_date == None) | (Ad.start_date <= now),
                    (Ad.end_date == None) | (Ad.end_date >= now)
                )
            )
            .order_by(func.random()) # Random rotation
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        ads = result.unique().scalars().all()
        
        return list(ads)

    async def track_view(self, ad_id: str, page_location: str = None, session_id: str = None):
        """Track an ad view and update revenue."""
        # Log event
        event = AdEvent(
            ad_id=ad_id,
            event_type=EventType.VIEW,
            page_location=page_location,
            user_session=session_id
        )
        self.db.add(event)
        
        # Update ad counts and revenue (CPM = cost per 1000 views)
        # Revenue = (views / 1000) * cpm_value
        # Since we are incrementing by 1 view, we add cpm_value / 1000 to revenue
        # SQL update is more atomic
        stmt = (
            update(Ad)
            .where(Ad.id == ad_id)
            .values(
                views_count=Ad.views_count + 1,
                revenue_generated=Ad.revenue_generated + (Ad.cpm_value / 1000.0)
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def track_click(self, ad_id: str, page_location: str = None, session_id: str = None) -> str | None:
        """Track an ad click, update revenue, and return the target URL."""
        # Log event
        event = AdEvent(
            ad_id=ad_id,
            event_type=EventType.CLICK,
            page_location=page_location,
            user_session=session_id
        )
        self.db.add(event)
        
        # Update ad counts and revenue (CPC = cost per click)
        stmt = (
            update(Ad)
            .where(Ad.id == ad_id)
            .values(
                click_count=Ad.click_count + 1,
                revenue_generated=Ad.revenue_generated + Ad.cpc_value
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Get the target URL
        query = select(Ad).options(
            selectinload(Ad.sponsor),
            selectinload(Ad.image)
        ).where(Ad.id == ad_id)
        result = await self.db.execute(query)
        ad = result.scalar_one_or_none()
        
        if not ad:
            return None
            
        if ad.ad_type == "sponsor" and ad.sponsor:
            return ad.sponsor.website_link
        elif ad.ad_type == "image" and ad.image:
            return ad.image.target_url
        
        return None
