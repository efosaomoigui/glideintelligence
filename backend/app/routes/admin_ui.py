from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import AIProvider, FeatureFlag, SourceHealth, User, Source, AIUsageLog

from app.utils.auth_deps import get_current_active_superuser_ui

router = APIRouter(prefix="/admin", tags=["admin-ui"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/settings")

@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from fastapi.responses import RedirectResponse
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
        
    providers_res = await db.execute(select(AIProvider))
    providers = providers_res.scalars().all()
    
    # flags_res = await db.execute(select(FeatureFlag))
    # flags = flags_res.scalars().all()
    flags = []
    
    health_res = await db.execute(select(SourceHealth))
    health = health_res.scalars().all()
    
    return templates.TemplateResponse("admin_settings.html", {
        "request": request,
        "providers": providers,
        "flags": flags,
        "health": health,
        "user": current_user_or_redirect,
        "active_page": "settings"
    })

@router.get("/users-ui", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from fastapi.responses import RedirectResponse
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
        
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "users": users,
        "user": current_user_or_redirect,
        "active_page": "users"
    })

@router.get("/usage", response_class=HTMLResponse)
async def admin_usage(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
        
    from app.models import AIUsageLog, Topic
    from sqlalchemy import func, desc
    from datetime import datetime, timedelta
    
    # Yesterday start
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Detailed logs
    logs_res = await db.execute(
        select(AIUsageLog, Topic.title)
        .outerjoin(Topic, AIUsageLog.topic_id == Topic.id)
        .order_by(AIUsageLog.timestamp.desc())
        .limit(50)
    )
    usage_logs = logs_res.all()
    
    # 2. Daily Summary (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    summary_res = await db.execute(
        select(
            func.date(AIUsageLog.timestamp).label('date'),
            func.sum(AIUsageLog.cost_usd).label('total_cost'),
            func.sum(AIUsageLog.tokens_used).label('total_tokens')
        )
        .where(AIUsageLog.timestamp >= seven_days_ago)
        .group_by(func.date(AIUsageLog.timestamp))
        .order_by(func.date(AIUsageLog.timestamp).desc())
    )
    daily_summary = summary_res.all()
    
    # 3. Provider breakdown (total)
    provider_res = await db.execute(
        select(
            AIUsageLog.provider_name,
            func.sum(AIUsageLog.cost_usd).label('cost'),
            func.sum(AIUsageLog.tokens_used).label('tokens'),
            func.count(AIUsageLog.id).label('calls')
        )
        .group_by(AIUsageLog.provider_name)
    )
    provider_breakdown = provider_res.all()

    return templates.TemplateResponse("admin_ai_usage.html", {
        "request": request,
        "user": current_user_or_redirect,
        "usage_logs": usage_logs,
        "daily_summary": daily_summary,
        "provider_breakdown": provider_breakdown,
        "active_page": "usage"
    })

@router.get("/sources-ui", response_class=HTMLResponse)
async def admin_sources(
    request: Request,
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from sqlalchemy import func

    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    
    offset = (page - 1) * limit
    
    # Total count for pagination
    total = await db.scalar(select(func.count(Source.id)))
    total_pages = (total + limit - 1) // limit
    
    result = await db.execute(select(Source).order_by(Source.id.desc()).offset(offset).limit(limit))
    sources = result.scalars().all()
    
    return templates.TemplateResponse("admin_sources.html", {
        "request": request,
        "sources": sources,
        "user": current_user_or_redirect,
        "active_page": "sources",
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    })

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from app.models.audit import AuditLog
    from app.models import Job, Topic, RawArticle, AIUsageLog
    from sqlalchemy import func, case
    from datetime import datetime, timedelta
    
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    
    # 1. Sources Stats
    source_count = await db.scalar(select(func.count(Source.id)))
    active_source_count = await db.scalar(select(func.count(Source.id)).where(Source.is_active == True))
    
    # 2. Jobs Stats (Last 24h)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    jobs_24h = await db.scalar(select(func.count(Job.id)).where(Job.started_at >= one_day_ago))
    failed_jobs = await db.scalar(select(func.count(Job.id)).where(Job.status == 'FAILED'))
    
    # 3. Topics Stats
    total_topics = await db.scalar(select(func.count(Topic.id)))
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    topics_today = await db.scalar(select(func.count(Topic.id)).where(Topic.created_at >= today_start))
    
    # 4. Article Volume (Today)
    from sqlalchemy import cast, TIMESTAMP
    today_count = await db.scalar(select(func.count(RawArticle.id)).where(cast(RawArticle.published_at, TIMESTAMP) >= today_start))

    # 6. AI Usage Stats (Today)
    ai_cost_today = await db.scalar(select(func.sum(AIUsageLog.cost_usd)).where(AIUsageLog.timestamp >= today_start)) or 0.0
    ai_tokens_today = await db.scalar(select(func.sum(AIUsageLog.tokens_used)).where(AIUsageLog.timestamp >= today_start)) or 0
    
    # AI Cost By Provider (Today)
    provider_usage_res = await db.execute(
        select(AIUsageLog.provider_name, func.sum(AIUsageLog.cost_usd))
        .where(AIUsageLog.timestamp >= today_start)
        .group_by(AIUsageLog.provider_name)
    )
    provider_costs = {name: cost for name, cost in provider_usage_res.all()}

    # 7. Recent Logs
    logs_res = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10))
    recent_logs = logs_res.scalars().all()
    
    # 6. Chart Data (Last 7 Days)
    # Helper to get daily counts
    async def get_daily_counts(model, date_col):
        data = []
        labels = []
        for i in range(6, -1, -1):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # Use date_col expression directly
            count = await db.scalar(
                select(func.count(model.id)).where(
                    date_col >= day_start,
                    date_col < day_end
                )
            )
            data.append(count or 0)
            labels.append(day_start.strftime('%a')) # Mon, Tue...
        return labels, data

    # Volume (Articles) - Cast String published_at to TIMESTAMP
    from sqlalchemy import cast, TIMESTAMP
    vol_labels, vol_data = await get_daily_counts(RawArticle, cast(RawArticle.published_at, TIMESTAMP))
    
    # Topics - created_at is already DateTime
    # vol_labels should be same for topics roughly
    _, topic_data = await get_daily_counts(Topic, Topic.created_at)

    # 7. Visitor / Engagement Stats
    total_views = await db.scalar(select(func.sum(Topic.view_count))) or 0
    top_viewed_topics_res = await db.execute(
        select(Topic.title, Topic.view_count, Topic.comment_count)
        .order_by(Topic.view_count.desc())
        .limit(5)
    )
    top_viewed_topics = top_viewed_topics_res.all()

    stats = {
        "total_sources": source_count or 0,
        "active_sources": active_source_count or 0,
        "jobs_24h": jobs_24h or 0,
        "failed_jobs": failed_jobs or 0,
        "total_topics": total_topics or 0,
        "topics_today": topics_today or 0,
        "today_count": today_count or 0,
        "ai_cost_today": ai_cost_today,
        "ai_tokens_today": ai_tokens_today,
        "provider_costs": provider_costs,
        "chart_labels": vol_labels,
        "volume_data": vol_data,
        "topic_data": topic_data,
        "total_views": total_views,
        "top_viewed_topics": top_viewed_topics,
    }
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_logs": recent_logs,
        "user": current_user_or_redirect,
        "active_page": "dashboard"
    })

@router.get("/jobs-ui", response_class=HTMLResponse)
async def admin_jobs_redirect():
    return RedirectResponse(url="/admin/pipeline")

@router.get("/pipeline", response_class=HTMLResponse)
async def admin_pipeline(
    request: Request,
    page: int = 1,
    limit: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from app.models import Job
    from sqlalchemy import select, func
    
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
        
    offset = (page - 1) * limit
    
    try:
        total = await db.scalar(select(func.count(Job.id)))
        # Order by started_at desc then ID desc for stable pagination
        result = await db.execute(
            select(Job)
            .order_by(Job.started_at.desc().nulls_first(), Job.id.desc())
            .offset(offset)
            .limit(limit)
        )
        jobs = result.scalars().all()
    except Exception:
        jobs = []
        total = 0

    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    # Simple Queue Stats (Approximate or via Redis ideally)
    # Using DB for now
    pending = await db.scalar(select(func.count(Job.id)).where(Job.status == 'PENDING'))
    active = await db.scalar(select(func.count(Job.id)).where(Job.status.in_(['RUNNING'])))
    failed = await db.scalar(select(func.count(Job.id)).where(Job.status == 'FAILED'))

    queue_stats = {
        "pending": pending or 0,
        "active": active or 0,
        "failed": failed or 0
    }
    
    return templates.TemplateResponse("admin_jobs.html", {
        "request": request,
        "jobs": jobs,
        "queue_stats": queue_stats,
        "user": current_user_or_redirect,
        "active_page": "pipeline",
         "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    })

@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    page: int = 1,
    limit: int = 50,
    search: str = "",
    level: str = "",
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from app.models.audit import AuditLog
    from sqlalchemy import or_, func

    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
        
    query = select(AuditLog)
    
    if search:
        search_fmt = f"%{search}%"
        query = query.where(or_(
            AuditLog.action.ilike(search_fmt),
            AuditLog.details.ilike(search_fmt),
            AuditLog.target.ilike(search_fmt)
        ))
    
    if level:
        # Assuming level is mapped to action (e.g. "ERROR" text in action) or if we had a level col
        # AuditLog usually has `action` like "LOGIN", "CREATE_SOURCE".
        # If user wants "levels", we might need to filter by string patterns for now.
        # "ERROR", "WARNING", "INFO"
        if level == "ERROR":
             query = query.where(or_(AuditLog.action.contains("ERROR"), AuditLog.action.contains("FAIL")))
        elif level == "WARNING":
             query = query.where(AuditLog.action.contains("WARN"))
        # else INFO is everything else? logic is fuzzy without dedicated column.
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    offset = (page - 1) * limit
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(limit)
    
    logs_res = await db.execute(query)
    logs = logs_res.scalars().all()
    
    return templates.TemplateResponse("admin_logs.html", {
        "request": request,
        "logs": logs,
        "user": current_user_or_redirect,
        "active_page": "logs",
        "filters": {"search": search, "level": level},
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    })

@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models import Topic
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Last 6 months labels + view aggregation per month using created_at as proxy
    # (view_count is cumulative, so we use it per topic grouped by created month)
    months_labels = []
    months_views = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if i == 0:
            month_end = now
        else:
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

        total = await db.scalar(
            select(func.coalesce(func.sum(Topic.view_count), 0))
            .where(Topic.created_at >= month_start)
            .where(Topic.created_at < month_end)
        ) or 0
        months_labels.append(month_start.strftime("%b %Y"))
        months_views.append(int(total))

    # Total stats
    total_views = await db.scalar(select(func.coalesce(func.sum(Topic.view_count), 0))) or 0
    total_comments = await db.scalar(select(func.coalesce(func.sum(Topic.comment_count), 0))) or 0
    total_topics = await db.scalar(select(func.count(Topic.id))) or 0

    # Top 10 topics by views
    top_res = await db.execute(
        select(Topic.title, Topic.category, Topic.view_count, Topic.comment_count)
        .order_by(Topic.view_count.desc())
        .limit(10)
    )
    top_topics = top_res.all()

    # Category breakdown
    cat_res = await db.execute(
        select(Topic.category, func.sum(Topic.view_count).label("views"))
        .group_by(Topic.category)
        .order_by(func.sum(Topic.view_count).desc())
        .limit(6)
    )
    category_breakdown = cat_res.all()

    return templates.TemplateResponse("admin_analytics.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "analytics",
        "months_labels": months_labels,
        "months_views": months_views,
        "total_views": int(total_views),
        "total_comments": int(total_comments),
        "total_topics": total_topics,
        "top_topics": top_topics,
        "category_breakdown": category_breakdown,
    })

@router.get("/polls", response_class=HTMLResponse)
async def admin_polls(
    request: Request,
    category: str = "",
    time_period: str = "all",
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    from fastapi.responses import RedirectResponse
    from app.models.interaction import Poll
    from app.models import Topic
    from sqlalchemy.orm import selectinload
    from datetime import datetime, timedelta, timezone
    
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    # Base query for polls
    query = select(Poll).join(Topic).options(
        selectinload(Poll.topic),
        selectinload(Poll.options)
    ).filter(Poll.is_active == True)

    # Apply category filter
    if category and category != "all":
        query = query.filter(Topic.category.ilike(category))

    # Apply time period filter
    now = datetime.utcnow()
    if time_period == "7days":
        query = query.filter(Poll.created_at >= now - timedelta(days=7))
    elif time_period == "30days":
        query = query.filter(Poll.created_at >= now - timedelta(days=30))
    elif time_period == "90days":
        query = query.filter(Poll.created_at >= now - timedelta(days=90))

    polls_res = await db.execute(query.order_by(Poll.created_at.desc()))
    polls = polls_res.scalars().all()
    
    # Calculate percentages for options
    for poll in polls:
        total = max(poll.total_votes, 1) # prevent division by zero
        for opt in poll.options:
            opt.percentage = int(round((opt.vote_count / total) * 100))

    return templates.TemplateResponse("admin_polls.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "polls",
        "polls": polls,
        "selected_category": category,
        "selected_time": time_period
    })

@router.get("/polls/{poll_id}/export", response_class=Response)
async def export_poll_pdf(
    poll_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.interaction import Poll
    from sqlalchemy.orm import selectinload
    from fastapi.responses import Response, JSONResponse

    result = await db.execute(
        select(Poll).options(selectinload(Poll.options)).where(Poll.id == poll_id)
    )
    poll = result.scalar_one_or_none()
    
    if not poll:
        return JSONResponse({"error": "Poll not found"}, status_code=404)
        
    topic_title = "General Context"
    if poll.topic_id:
        from app.models import Topic
        topic_res = await db.execute(select(Topic).where(Topic.id == poll.topic_id))
        topic = topic_res.scalar_one_or_none()
        if topic:
            topic_title = topic.title

    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from datetime import datetime

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], spaceAfter=20)
    elements.append(Paragraph("Poll Results Report", title_style))
    
    # Context
    elements.append(Paragraph(f"<b>Topic:</b> {topic_title}", styles['Normal']))
    elements.append(Paragraph(f"<b>Question:</b> {poll.question}", styles['Heading2']))
    elements.append(Paragraph(f"<b>Total Votes:</b> {poll.total_votes}", styles['Normal']))
    elements.append(Paragraph(f"<b>Export Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Breakdown Table
    data = [["Option", "Votes", "Percentage"]]
    for opt in sorted(poll.options, key=lambda x: x.vote_count, reverse=True):
        pct = (opt.vote_count / poll.total_votes * 100) if poll.total_votes > 0 else 0
        data.append([opt.option_text, str(opt.vote_count), f"{pct:.1f}%"])

    table = Table(data, colWidths=[250, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()

    headers = {
        'Content-Disposition': f'attachment; filename="poll_{poll_id}_export.pdf"',
        'Content-Type': 'application/pdf',
    }
    
    return Response(content=pdf_bytes, headers=headers)

@router.get("/polls/{poll_id}/backup")
async def backup_poll(
    poll_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.interaction import Poll
    from sqlalchemy.orm import selectinload
    from fastapi.responses import JSONResponse
    import json
    from datetime import datetime

    result = await db.execute(
        select(Poll).options(selectinload(Poll.options)).where(Poll.id == poll_id)
    )
    poll = result.scalar_one_or_none()
    
    if not poll:
        return JSONResponse({"error": "Poll not found"}, status_code=404)

    # Mark as backed up
    poll.is_backed_up = True
    await db.commit()

    # Construct JSON payload
    data = {
        "id": poll.id,
        "question": poll.question,
        "topic_id": poll.topic_id,
        "total_votes": poll.total_votes,
        "created_at": poll.created_at.isoformat() if poll.created_at else None,
        "options": [
            {"text": opt.option_text, "votes": opt.vote_count} for opt in poll.options
        ]
    }

    # Serve JSON file download
    json_str = json.dumps(data, indent=2)
    filename = f"poll_backup_{poll_id}_{datetime.now().strftime('%Y%m%d%H%M')}.json"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'application/json',
    }
    return Response(content=json_str, headers=headers)

@router.delete("/polls/backed_up")
async def delete_backed_up_polls(
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.interaction import Poll
    from fastapi.responses import JSONResponse
    from sqlalchemy import delete

    # Delete all polls marked as backed up. 
    # SQLAlchemy will cascade delete poll_options and poll_votes due to our model relationships.
    result = await db.execute(delete(Poll).where(Poll.is_backed_up == True))
    await db.commit()
    
    return JSONResponse({"message": f"Successfully deleted {result.rowcount} backed up polls."})

@router.get("/comments", response_class=HTMLResponse)
async def admin_comments(
    request: Request,
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models import Topic
    from sqlalchemy.orm import selectinload
    from sqlalchemy import func

    # Get topics with comments, optionally filter by title Search
    query = select(Topic).where(Topic.comment_count > 0)
    
    if search:
        query = query.filter(Topic.title.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count(Topic.id)).where(Topic.comment_count > 0)
    if search:
        count_query = count_query.filter(Topic.title.ilike(f"%{search}%"))
    
    total = await db.scalar(count_query) or 0
    total_pages = (total + limit - 1) // limit
    
    # Paginate
    offset = (page - 1) * limit
    topics_res = await db.execute(query.order_by(Topic.created_at.desc()).offset(offset).limit(limit))
    topics = topics_res.scalars().all()

    return templates.TemplateResponse("admin_comments.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "comments",
        "topics": topics,
        "search_query": search,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    })

@router.get("/comments/topic/{topic_id}", response_class=HTMLResponse)
async def admin_comments_detail(
    topic_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models import Topic
    from app.models.interaction import Comment
    from sqlalchemy.orm import selectinload

    # Fetch Topic
    topic_res = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = topic_res.scalar_one_or_none()
    
    if not topic:
        return RedirectResponse("/admin/comments")

    # Fetch Comments
    comments_res = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.topic_id == topic_id)
        .order_by(Comment.created_at.desc())
    )
    comments = comments_res.scalars().all()

    return templates.TemplateResponse("admin_comments_detail.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "comments",
        "topic": topic,
        "comments": comments
    })

@router.get("/comments/topic/{topic_id}/export", response_class=Response)
async def export_topic_comments_pdf(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models import Topic
    from app.models.interaction import Comment
    from sqlalchemy.orm import selectinload
    from fastapi.responses import JSONResponse, Response
    
    # Needs reportlab and IO
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    # Fetch Topic
    topic_res = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = topic_res.scalar_one_or_none()
    
    if not topic:
        return JSONResponse({"error": "Topic not found"}, status_code=404)

    # Fetch Comments
    comments_res = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.topic_id == topic_id)
        .order_by(Comment.created_at.asc())
    )
    comments = comments_res.scalars().all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], spaceAfter=10)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], textColor='grey', spaceAfter=20)
    commenter_style = ParagraphStyle('Commenter', parent=styles['Heading3'], spaceAfter=2)
    comment_body_style = ParagraphStyle('CommentBody', parent=styles['Normal'], spaceAfter=15)

    # Header
    elements.append(Paragraph("Community Thread Report", title_style))
    elements.append(Paragraph(f"<b>Topic:</b> {topic.title}", styles['Heading2']))
    elements.append(Paragraph(f"<b>Category:</b> {topic.category} | <b>Total Comments:</b> {len(comments)}", meta_style))
    elements.append(Spacer(1, 10))

    # Comments
    for c in comments:
        user_id = f"@{c.user.username}" if c.user.username else f"@{c.user.email.split('@')[0]}"
        time_str = c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else 'Unknown'
        
        elements.append(Paragraph(f"<b>{user_id}</b> <font color='grey'>on {time_str}</font>", commenter_style))
        elements.append(Paragraph(c.content, comment_body_style))

    if not comments:
        elements.append(Paragraph("No comments found for this topic.", styles['Normal']))

    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()

    headers = {
        'Content-Disposition': f'attachment; filename="topic_{topic_id}_comments.pdf"',
        'Content-Type': 'application/pdf',
    }
    
    return Response(content=pdf_bytes, headers=headers)

    # ------------------------------------------
    # ADS MANAGER UI ROUTES
    # ------------------------------------------

@router.get("/ads", response_class=HTMLResponse)
async def admin_ads_list(
    request: Request,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.ads import Ad
    from sqlalchemy import func
    
    # Pagination
    offset = (page - 1) * limit
    total = await db.scalar(select(func.count(Ad.id))) or 0
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    # Fetch ads
    ads_res = await db.execute(
        select(Ad).order_by(Ad.created_at.desc()).offset(offset).limit(limit)
    )
    ads = ads_res.scalars().all()
    
    # Calculate global stats
    active_ads = await db.scalar(select(func.count(Ad.id)).where(Ad.status == "active")) or 0
    total_views = await db.scalar(select(func.sum(Ad.views_count))) or 0
    total_clicks = await db.scalar(select(func.sum(Ad.click_count))) or 0
    total_revenue = await db.scalar(select(func.sum(Ad.revenue_generated))) or 0.0

    stats = {
        "active_ads": active_ads,
        "total_views": total_views,
        "total_clicks": total_clicks,
        "total_revenue": total_revenue
    }

    return templates.TemplateResponse("admin_ads.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "ads",
        "ads": ads,
        "stats": stats,
        "pagination": {
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    })

@router.get("/ads/create", response_class=HTMLResponse)
async def admin_ads_create_view(
    request: Request,
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    return templates.TemplateResponse("admin_ads_form.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "ads",
        "is_edit": False,
        "ad": None
    })

@router.post("/ads/create")
async def admin_ads_create_post(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.ads import Ad, AdStatus, AdType, AdExternalNetwork, AdSponsor, AdImage
    
    form = await request.form()
    
    try:
        ad = Ad(
            ad_type=AdType(form.get("ad_type")),
            title=form.get("title"),
            status=AdStatus(form.get("status", "active")),
            placement_group=form.get("placement_group", "homepage_feed"),
            priority=int(form.get("priority") or 0),
            cpm_value=float(form.get("cpm_value") or 0.0),
            cpc_value=float(form.get("cpc_value") or 0.0)
        )
        db.add(ad)
        await db.flush() # flush to get ad.id
        
        # Add sub-type models based on type
        if ad.ad_type == AdType.EXTERNAL:
            ext = AdExternalNetwork(
                ad_id=ad.id,
                network_name=form.get("ext_network_name", ""),
                ad_size=form.get("ext_ad_size"),
                script_code=form.get("ext_script_code", "")
            )
            db.add(ext)
            
        elif ad.ad_type == AdType.SPONSOR:
            spon = AdSponsor(
                ad_id=ad.id,
                tagline=form.get("sponsor_tagline"),
                summary=form.get("sponsor_summary"),
                full_content=form.get("sponsor_full_content"),
                image_url=form.get("sponsor_image_url"),
                cta_text=form.get("sponsor_cta_text", "Learn More"),
                website_link=form.get("sponsor_website_link")
            )
            db.add(spon)
            
        elif ad.ad_type == AdType.IMAGE:
            img = AdImage(
                ad_id=ad.id,
                image_url=form.get("img_url", ""),
                target_url=form.get("img_target", ""),
                alt_text=form.get("img_alt"),
                ad_size=form.get("img_size")
            )
            db.add(img)

        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error creating ad: {e}")
        
    return RedirectResponse(url="/admin/ads", status_code=303)

@router.get("/ads/edit/{ad_id}", response_class=HTMLResponse)
async def admin_ads_edit_view(
    ad_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.ads import Ad
    from sqlalchemy.orm import selectinload
    
    res = await db.execute(
        select(Ad).options(
            selectinload(Ad.external),
            selectinload(Ad.sponsor),
            selectinload(Ad.image)
        ).where(Ad.id == ad_id)
    )
    ad = res.scalar_one_or_none()
    
    if not ad:
        return RedirectResponse(url="/admin/ads")

    return templates.TemplateResponse("admin_ads_form.html", {
        "request": request,
        "user": current_user_or_redirect,
        "active_page": "ads",
        "is_edit": True,
        "ad": ad
    })

@router.post("/ads/edit/{ad_id}")
async def admin_ads_edit_post(
    ad_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.ads import Ad, AdStatus, AdType
    from sqlalchemy.orm import selectinload
    
    res = await db.execute(
        select(Ad).options(
            selectinload(Ad.external),
            selectinload(Ad.sponsor),
            selectinload(Ad.image)
        ).where(Ad.id == ad_id)
    )
    ad = res.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/admin/ads")
        
    form = await request.form()
    
    try:
        # Update base stats
        ad.title = form.get("title", ad.title)
        ad.status = AdStatus(form.get("status", ad.status))
        ad.placement_group = form.get("placement_group", ad.placement_group)
        ad.priority = int(form.get("priority") or 0)
        ad.cpm_value = float(form.get("cpm_value") or 0.0)
        ad.cpc_value = float(form.get("cpc_value") or 0.0)
        
        # Update type specifics
        if ad.ad_type == AdType.EXTERNAL and ad.external:
            ad.external.network_name = form.get("ext_network_name", "")
            ad.external.ad_size = form.get("ext_ad_size")
            ad.external.script_code = form.get("ext_script_code", "")
            
        elif ad.ad_type == AdType.SPONSOR and ad.sponsor:
            ad.sponsor.tagline = form.get("sponsor_tagline")
            ad.sponsor.summary = form.get("sponsor_summary")
            ad.sponsor.full_content = form.get("sponsor_full_content")
            ad.sponsor.image_url = form.get("sponsor_image_url")
            ad.sponsor.cta_text = form.get("sponsor_cta_text", "Learn More")
            ad.sponsor.website_link = form.get("sponsor_website_link")
            
        elif ad.ad_type == AdType.IMAGE and ad.image:
            ad.image.image_url = form.get("img_url", "")
            ad.image.target_url = form.get("img_target", "")
            ad.image.alt_text = form.get("img_alt")
            ad.image.ad_size = form.get("img_size")

        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error updating ad: {e}")
        
    return RedirectResponse(url="/admin/ads", status_code=303)

@router.get("/ads/delete/{ad_id}")
async def admin_ads_delete(
    ad_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_or_redirect = Depends(get_current_active_superuser_ui)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect

    from app.models.ads import Ad
    res = await db.execute(select(Ad).where(Ad.id == ad_id))
    ad = res.scalar_one_or_none()
    
    if ad:
        await db.delete(ad)
        await db.commit()
        
    return RedirectResponse(url="/admin/ads", status_code=303)

@router.get("/logout")
async def admin_logout(request: Request):
    # Note: We can't easily log logout because the cookie is about to be deleted
    # and we don't have the user context without parsing the token manually.
    # Login events are logged, which is sufficient for most audit needs.
    
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response
