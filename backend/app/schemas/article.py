from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ArticleEntitySchema(BaseModel):
    entity_name: str
    entity_type: str
    confidence: float

    model_config = ConfigDict(from_attributes=True)

class ArticleBase(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    image_url: Optional[str] = None
    sentiment_score: Optional[float] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ArticleSchema(ArticleBase):
    id: int
    source_id: int
    source_name: Optional[str] = None # To be populated by service join
    
    # Hero / Deep Dive specific fields
    source_count: Optional[int] = 0
    comment_count: Optional[int] = 0
    summary: Optional[str] = None
    bullets: Optional[List[str]] = []
    
    model_config = ConfigDict(from_attributes=True)

class ArticleDetailSchema(ArticleSchema):
    content: str
    entities: List[ArticleEntitySchema] = []
    
    model_config = ConfigDict(from_attributes=True)
