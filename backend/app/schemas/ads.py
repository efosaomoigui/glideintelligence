from pydantic import BaseModel, HttpUrl, UUID4, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AdType(str, Enum):
    EXTERNAL = "external"
    SPONSOR = "sponsor"
    IMAGE = "image"

class AdStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

class AdPlacementGroup(str, Enum):
    HERO_SPOTLIGHT = "hero_spotlight"
    HOMEPAGE_FEED = "homepage_feed"
    HOMEPAGE_SIDEBAR = "homepage_sidebar"
    VERTICAL_FEED = "vertical_feed"
    VERTICAL_SIDEBAR = "vertical_sidebar"
    SIDEBAR_CARD = "sidebar_card"
    TOPIC_DETAIL = "topic_detail"
    
    # Specific category feeds
    POLITICS_FEED = "politics_feed"
    POLITICS_SIDEBAR = "politics_sidebar"
    BUSINESS_FEED = "business_feed"
    BUSINESS_SIDEBAR = "business_sidebar"
    ECONOMY_FEED = "economy_feed"
    ECONOMY_SIDEBAR = "economy_sidebar"
    TECHNOLOGY_FEED = "technology_feed"
    TECHNOLOGY_SIDEBAR = "technology_sidebar"
    SECURITY_FEED = "security_feed"
    SECURITY_SIDEBAR = "security_sidebar"
    SPORT_FEED = "sport_feed"
    SPORT_SIDEBAR = "sport_sidebar"
    REGIONAL_FEED = "regional_feed"
    REGIONAL_SIDEBAR = "regional_sidebar"
    GLOBAL_IMPACT_FEED = "global-impact_feed"
    GLOBAL_IMPACT_SIDEBAR = "global-impact_sidebar"
    SOCIAL_FEED = "social_feed"
    SOCIAL_SIDEBAR = "social_sidebar"
    ENVIRONMENT_FEED = "environment_feed"
    ENVIRONMENT_SIDEBAR = "environment_sidebar"
    GENERAL_FEED = "general_feed"
    GENERAL_SIDEBAR = "general_sidebar"

# Base common fields
class AdBase(BaseModel):
    title: str
    status: AdStatus = AdStatus.ACTIVE
    placement_group: AdPlacementGroup
    priority: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    cpm_value: float = 0.0
    cpc_value: float = 0.0

# Subtype schemas
class AdExternalNetworkBase(BaseModel):
    network_name: str
    ad_size: Optional[str] = None
    script_code: str
    is_rotating: bool = True
    display_on_homepage: bool = True

class AdSponsorBase(BaseModel):
    tagline: Optional[str] = None
    summary: Optional[str] = None
    full_content: Optional[str] = None
    image_url: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_link: Optional[str] = None
    cta_text: str = "Learn More"

class AdImageBase(BaseModel):
    image_url: str
    target_url: str
    alt_text: Optional[str] = None
    ad_size: Optional[str] = None


# Create incoming schemas
class AdCreate(AdBase):
    ad_type: AdType
    external: Optional[AdExternalNetworkBase] = None
    sponsor: Optional[AdSponsorBase] = None
    image: Optional[AdImageBase] = None

class AdUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[AdStatus] = None
    placement_group: Optional[AdPlacementGroup] = None
    priority: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    cpm_value: Optional[float] = None
    cpc_value: Optional[float] = None
    external: Optional[AdExternalNetworkBase] = None
    sponsor: Optional[AdSponsorBase] = None
    image: Optional[AdImageBase] = None

# Detail out schemas
class AdExternalNetworkResponse(AdExternalNetworkBase):
    id: str

class AdSponsorResponse(AdSponsorBase):
    id: str

class AdImageResponse(AdImageBase):
    id: str

class AdResponse(AdBase):
    id: str
    ad_type: AdType
    views_count: int
    click_count: int
    revenue_generated: float
    created_at: datetime
    updated_at: datetime
    
    external: Optional[AdExternalNetworkResponse] = None
    sponsor: Optional[AdSponsorResponse] = None
    image: Optional[AdImageResponse] = None

    class Config:
        from_attributes = True

class AdAnalyticsResponse(BaseModel):
    ad_id: str
    views: int
    clicks: int
    revenue: float
