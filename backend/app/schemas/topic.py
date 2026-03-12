from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.article import ArticleSchema

class TopicAnalysisSchema(BaseModel):
    summary: str
    key_points: Optional[List[str]] = None
    regional_framing: Optional[dict] = None
    
    # Intelligence Agent Fields
    executive_summary: Optional[str] = None
    what_you_need_to_know: Optional[List[str]] = None
    key_takeaways: Optional[List[str]] = None
    drivers_of_story: Optional[List[str]] = None
    strategic_implications: Optional[List[str]] = None
    regional_impact: Optional[List[str]] = None
    confidence_score: Optional[float] = 0.0
    
    sentiment_summary: Optional[str] = None
    framing_overview: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class TopicSentimentSchema(BaseModel):
    positive: float
    neutral: float
    negative: float
    model_config = ConfigDict(from_attributes=True)

class TopicTrendSchema(BaseModel):
    date: datetime
    interest_score: float
    model_config = ConfigDict(from_attributes=True)

class TopicVideoSchema(BaseModel):
    video_url: str
    title: str
    thumbnail_url: Optional[str] = None
    duration: Optional[str] = None
    source_platform: str
    model_config = ConfigDict(from_attributes=True)

class SentimentDimensionSchema(BaseModel):
    dimension_type: str
    dimension_value: str
    sentiment: str
    sentiment_score: float
    percentage: float
    icon: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SourcePerspectiveSchema(BaseModel):
    source_name: str
    source_type: Optional[str] = None
    frame_label: str
    sentiment: str
    sentiment_percentage: str
    key_narrative: str
    model_config = ConfigDict(from_attributes=True)

class RegionalImpactSchema(BaseModel):
    impact_category: Optional[str] = None
    icon: Optional[str] = None
    title: str
    value: str
    severity: Optional[str] = None
    context: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RegionalCategorySchema(BaseModel):
    region_name: str
    impact: str = "Neutral"
    model_config = ConfigDict(from_attributes=True)

class IntelligenceCardSchema(BaseModel):
    category: str
    icon: str
    title: str
    description: str
    trend_percentage: str
    is_positive: bool
    model_config = ConfigDict(from_attributes=True)

class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_trending: bool = False

class TopicSchema(TopicBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TopicTrendingSchema(TopicSchema):
    article_count: int = 0
    source_count: int = 0
    # Core Topic fields also needed by frontend
    category: Optional[str] = None
    overall_sentiment: Optional[str] = "neutral"
    sentiment_score: Optional[float] = 0.0
    # Frontend specific fields (computed/derived)
    badge: Optional[str] = "Trending"
    ai_brief: Optional[str] = None
    bullets: List[str] = []
    updated_at_str: Optional[str] = None
    perspectives: List[dict] = Field(default=[], validation_alias="frontend_perspectives")
    impact: List[dict] = []
    sources: List[dict] = []
    engagement: dict = {}
    sentiment_breakdown: List[SentimentDimensionSchema] = []
    # These are populated from private attrs set in _enrich_topic_for_frontend
    regional_impacts: List[RegionalImpactSchema] = []
    regional_categories: List[RegionalCategorySchema] = []
    
    # Intelligence Indicators
    intelligence_level: str = "Standard"
    is_premium: bool = False
    analysis_status: Optional[str] = None
    
    # Analysis object — included so home page can access what_you_need_to_know etc.
    analysis: Optional[TopicAnalysisSchema] = None
    
    # Enhanced Metadata
    key_takeaways: Optional[str] = None
    core_drivers: List[str] = []
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


    @model_validator(mode='before')
    @classmethod
    def extract_private_data(cls, values: Any) -> Any:
        """Convert enriched ORM object to dict so private attrs (_perspectives_data etc)
        are accessible without going through SQLAlchemy instrumented descriptors."""
        if not hasattr(values, '__dict__'):
            return values  # already a dict, pass through

        obj_dict = values.__dict__  # raw Python __dict__, includes private attrs

        # Build a flat dict of all fields Pydantic needs
        data: dict = {}

        # Standard ORM columns (safe to read via getattr since they're columns, not relationships)
        for col in ('id', 'title', 'description', 'is_trending', 'category',
                    'overall_sentiment', 'sentiment_score', 'status', 'badge',
                    'source_count', 'article_count', 'created_at', 'updated_at',
                    'view_count', 'analysis_status'):
            try:
                val = getattr(values, col, None)
                if val is not None:
                    data[col] = val
            except Exception:
                pass

        # Frontend-enriched attrs (computed strings or plain dicts)
        for attr in ('ai_brief', 'bullets', 'updated_at_str', 'sources', 'engagement', 'intelligence_level', 'is_premium', 'impact'):
            val = obj_dict.get(attr)
            if val is not None:
                data[attr] = val

        # Relationship-based fields: ONLY read if in obj_dict (meaning they were loaded or explicitly set)
        for rel in ('analysis', 'articles', 'intelligence_card', 'trends', 'videos', 'sentiment_breakdown', 'regional_categories'):
            if rel in obj_dict:
                val = getattr(values, rel, None)
                if val is not None:
                    # Convert to list if it's a collection
                    data[rel] = list(val) if isinstance(val, (list, tuple)) or hasattr(val, '__iter__') and not isinstance(val, (dict, str)) else val
            else:
                # Default to empty/None for missing relationships to avoid 500s on transition objects
                if rel in ('articles', 'trends', 'videos', 'sentiment_breakdown', 'regional_categories'):
                    data[rel] = []
                else:
                    data[rel] = None

        # sentiment_breakdown is an ORM relationship — only read if loaded
        if 'sentiment_breakdown' in obj_dict:
            data['sentiment_breakdown'] = list(getattr(values, 'sentiment_breakdown', []) or [])
        else:
            data['sentiment_breakdown'] = []

        # Private enriched data — read from raw __dict__ to bypass SQLAlchemy descriptors
        data['source_perspectives'] = obj_dict.get('_perspectives_data') or []
        data['regional_impacts'] = obj_dict.get('_impacts_data') or []
        
        # Enhanced metadata
        metadata = obj_dict.get('metadata_') or {}
        data['key_takeaways'] = metadata.get('key_takeaways')
        data['core_drivers'] = metadata.get('core_drivers', [])

        return data

class TopicDetailSchema(TopicTrendingSchema):
    # Engagement counters — needed by the flyout to read real DB values
    view_count: int = 0
    comment_count: int = 0
    analysis: Optional[TopicAnalysisSchema] = None
    # sentiment_breakdown can be list or object depending on context, using list for detail view
    sentiment_breakdown: List[SentimentDimensionSchema] = [] 
    source_perspectives: List[SourcePerspectiveSchema] = []
    regional_impacts: List[RegionalImpactSchema] = []
    regional_categories: List[RegionalCategorySchema] = []
    intelligence_card: Optional[IntelligenceCardSchema] = None
    
    trends: List[TopicTrendSchema] = []
    videos: List[TopicVideoSchema] = []
    articles: List[ArticleSchema] = []
    
    model_config = ConfigDict(from_attributes=True)
