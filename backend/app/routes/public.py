from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.services.news_service import NewsService
from app.schemas.base import PaginatedResponse, PaginationParams
from app.schemas.topic import TopicSchema, TopicTrendingSchema, TopicDetailSchema
from app.schemas.article import ArticleSchema
from app.schemas.user import UserCreate, UserSchema
from app.models.user import User
from app.utils.security import get_password_hash
from app.utils.cache import cached

router = APIRouter(prefix="/api", tags=["public"])

class HomeResponse(BaseModel):
    trending_topics: List[TopicTrendingSchema]
    latest_articles: List[ArticleSchema]
    hero_article: Optional[ArticleSchema] = None
    pulse: Dict[str, Any]

class VerticalStats(BaseModel):
    active_topics: int = 0
    total_sources: int = 0
    total_views: int = 0
    update_freq: str = "Real-time"

class VerticalResponse(BaseModel):
    topics: List[TopicTrendingSchema]
    featured_articles: List[ArticleSchema]
    category: str
    pulse: Optional[Dict[str, Any]] = None
    stats: Optional[VerticalStats] = None

class SidebarPulse(BaseModel):
    sentiment_label: str
    sentiment_score: float
    sentiment_text: str
    trending_topic: str
    trending_text: str
    regional_focus: str
    regional_text: str

class SidebarVoice(BaseModel):
    initials: str
    name: str
    role: str
    quote: str
    color: str

class SidebarPoll(BaseModel):
    question: str
    options: List[str]
    responses: int
    closes_in_hours: int

class SidebarResponse(BaseModel):
    pulse: SidebarPulse
    voices: List[SidebarVoice]
    poll: SidebarPoll

@router.get("/home", response_model=HomeResponse)
@cached(ttl=600, prefix="home")
async def get_home(db: AsyncSession = Depends(get_db)):
    service = NewsService(db)
    data = await service.get_home_data()
    return data

@router.post("/users", response_model=UserSchema)
async def create_public_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Return existing user for this lightweight identity flow
        return existing_user
        
    # Create new lightweight user with a fake password (not intended for real login yet)
    import secrets
    user = User(
        email=user_in.email,
        username=user_in.email.split("@")[0] + "_" + secrets.token_hex(4),
        hashed_password=get_password_hash(user_in.password if hasattr(user_in, 'password') else secrets.token_urlsafe(16)),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False,
        role="user",
        is_verified=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/sidebar", response_model=SidebarResponse)
@cached(ttl=300, prefix="sidebar")
async def get_sidebar(db: AsyncSession = Depends(get_db)):
    service = NewsService(db)
    home_data = await service.get_home_data()
    topics = home_data.get("trending_topics", [])
    pulse_raw = home_data.get("pulse", {})

    sentiment = pulse_raw.get("sentiment", {})
    context = pulse_raw.get("context", {})
    regional = pulse_raw.get("regional", {})

    # Parse sentiment score from string like "+12%" -> 62 (adding 50 base for bar width)
    score_str = sentiment.get("score", "0%").replace("%", "").replace("+", "")
    try:
        raw_score = float(score_str)
    except ValueError:
        raw_score = 0.0
    bar_pct = min(100.0, max(0.0, 50.0 + raw_score))

    pulse = SidebarPulse(
        sentiment_label=sentiment.get("label", "Neutral"),
        sentiment_score=bar_pct,
        sentiment_text=sentiment.get("text", "Tracking ongoing developments."),
        trending_topic=context.get("name", topics[0].title if topics else "Top Story"),
        trending_text=context.get("description", "Dominating coverage this period."),
        regional_focus=regional.get("name", "ECOWAS"),
        regional_text=regional.get("description", "Monitoring cross-border developments."),
    )

    # 1. Fetch REAL Community Voices (Hot Comments)
    voices_data = await service.get_hot_comments(limit=4)
    if voices_data:
        voices = [SidebarVoice(**v) for v in voices_data]
    else:
        # Fallback to topic-based mock if no comments exist
        VOICE_META = [
            {"initials": "OA", "name": "Olumide Adegoke", "role": "Financial Analyst", "color": "#c0392b"},
            {"initials": "NK", "name": "Ngozi Kalu",      "role": "Policy Expert",      "color": "#27ae60"},
            {"initials": "CM", "name": "Chidi Musa",       "role": "Political Analyst",  "color": "#2980b9"},
        ]
        voices = []
        for i, meta in enumerate(VOICE_META):
            if i < len(topics):
                topic = topics[i]
                brief = getattr(topic, "ai_brief", None) or getattr(topic, "description", "") or ""
                quote = brief[:120].rstrip() + ("..." if len(brief) > 120 else "")
            else:
                quote = "Monitoring ongoing developments across multiple sectors."
            voices.append(SidebarVoice(**meta, quote=quote))

    # 2. Fetch REAL Hot Poll
    real_poll = await service.get_hot_poll()
    if real_poll:
        poll = SidebarPoll(
            question=real_poll["question"],
            options=[o["option_text"] for o in real_poll["options"]],
            responses=real_poll.get("total_votes", 0),
            closes_in_hours=24, # Could derive from closes_at if available
        )
    else:
        # Fallback to contextual mock
        poll_topic = topics[0] if topics else None
        poll_question = (
            f"How will {poll_topic.title[:60]}... affect you?" if poll_topic
            else "How do you assess this week's economic developments?"
        )
        poll = SidebarPoll(
            question=poll_question,
            options=["Very positively", "Somewhat positively", "No significant impact", "Negatively"],
            responses=max(124, sum(getattr(t, "comment_count", 0) for t in topics[:3]) * 2),
            closes_in_hours=24,
        )

    return SidebarResponse(pulse=pulse, voices=voices, poll=poll)

def random_responses(topics) -> int:
    """Derive a plausible response count from topic engagement data."""
    total = 0
    for t in topics[:3]:
        total += getattr(t, "comment_count", 0) or 0
    return max(124, total * 2)

@router.get("/topics/trending", response_model=PaginatedResponse[TopicTrendingSchema])
@cached(ttl=300, prefix="trending")
async def get_trending_topics(
    filter: str = Query("all", pattern="^(all|today|week|month|developing)$"),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    service = NewsService(db)
    items, total = await service.get_trending_topics(
        page=params.page, 
        limit=params.limit, 
        filter_type=filter, 
        category=category,
        region=region
    )
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        limit=params.limit,
        has_more=(params.page * params.limit) < total
    )

@router.get("/vertical/{name}", response_model=VerticalResponse)
async def get_vertical_data(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """Return full vertical data including dynamic stats. No caching — stats must be live."""
    service = NewsService(db)
    data = await service.get_vertical_data(name)
    return data

@router.get("/topic/slug/{slug}", response_model=TopicDetailSchema)
async def get_topic_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    # Convert slug to title (e.g. "inflation-surge" -> "Inflation Surge")
    title = slug.replace("-", " ")
    service = NewsService(db)
    topic = await service.get_topic_by_title(title)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@router.get("/topic/{topic_id}", response_model=TopicDetailSchema)
async def get_topic_detail(
    topic_id: int,
    db: AsyncSession = Depends(get_db)
):
    # NOTE: deliberately NOT cached — view_count and comment_count must be live
    service = NewsService(db)
    topic = await service.get_topic_detail(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@router.post("/topic/{topic_id}/view")
async def track_topic_view(
    topic_id: int,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import update
    from app.models.topic import Topic
    result = await db.execute(
        update(Topic).where(Topic.id == topic_id).values(view_count=Topic.view_count + 1).returning(Topic.view_count)
    )
    await db.commit()
    new_count = result.scalar_one_or_none()
    return {"status": "ok", "view_count": new_count}

@router.get("/search")
async def search(
    q: str = Query(..., min_length=2),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Search both processed topics AND source articles. Topics are returned first."""
    service = NewsService(db)
    topics, topics_total = await service.search_topics(q, page=1, limit=10)
    articles, art_total = await service.search_articles(q, params.page, params.limit)
    return {
        "topics": topics,
        "articles": articles,
        "topics_total": topics_total,
        "total": art_total,
        "page": params.page,
        "limit": params.limit,
        "has_more": (params.page * params.limit) < art_total,
    }

@router.get("/article/{article_id}", response_model=ArticleSchema)
@cached(ttl=300, prefix="article")
async def get_article_detail(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = NewsService(db)
    article = await service.get_article_detail(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
