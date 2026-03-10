from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ad_service import AdService
from app.schemas.ads import AdResponse

router = APIRouter(prefix="/api/ads", tags=["ads"])

@router.get("/placement/{placement_group}", response_model=AdResponse)
async def get_ad_for_placement(
    placement_group: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch an active ad for a specific placement group to display in the frontend."""
    # placement_group could be 'homepage_feed', 'article_sidebar', etc.
    service = AdService(db)
    ad = await service.get_ad_for_placement(placement_group)
    
    if not ad:
        raise HTTPException(status_code=404, detail="No active ads for this placement")
        
    return ad

@router.post("/render/{ad_id}")
async def track_ad_view(
    ad_id: str,
    request: Request,
    page_location: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Track that an ad was viewed on screen (e.g. via IntersectionObserver)."""
    # Try to get some session identifier (could be IP, or user token if available)
    session_id = request.client.host if request.client else None
    
    service = AdService(db)
    # Fire and forget / background task might be better, but doing it inline for simplicity
    try:
        await service.track_view(
            ad_id=ad_id, 
            page_location=page_location,
            session_id=session_id
        )
        return {"status": "success", "event": "view"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/click/{ad_id}")
async def track_ad_click(
    ad_id: str,
    request: Request,
    page_location: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Track an ad click and redirect the user to the target URL."""
    session_id = request.client.host if request.client else None
    
    service = AdService(db)
    try:
        target_url = await service.track_click(
            ad_id=ad_id, 
            page_location=page_location,
            session_id=session_id
        )
        
        if target_url:
            return RedirectResponse(url=target_url)
        else:
            return {"status": "success", "event": "click", "message": "Click tracked, but no target URL specified"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
