from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.settings import AIProviderType

class AIProviderCreate(BaseModel):
    name: str
    type: AIProviderType
    api_key: Optional[str] = None
    model: str
    enabled: bool = True
    priority: int = 0

class AIProviderSchema(AIProviderCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FeatureFlagUpdate(BaseModel):
    key: str
    enabled: bool

class FeatureFlagSchema(FeatureFlagUpdate):
    id: int
    
    class Config:
        from_attributes = True

class SourceHealthSchema(BaseModel):
    source_id: int
    status: str
    last_success: Optional[datetime]
    fail_count: int

    class Config:
        from_attributes = True
