from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import datetime
import asyncio

from app.database import get_db
from app.models import Job, AIProvider, FeatureFlag, SourceHealth, Source
from app.models.user import User
from app.workers import tasks
from app.schemas.settings import AIProviderSchema, AIProviderCreate, FeatureFlagSchema, FeatureFlagUpdate, SourceHealthSchema

from app.utils.auth_deps import get_current_active_superuser
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_active_superuser)])

@router.post("/settings/maintenance/clean-pipeline")
async def clean_pipeline_maintenance(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Trigger a full database cleanup of pipeline data."""
    from app.services.maintenance_service import clean_pipeline_data
    from app.services.audit_service import log_action
    
    result = await clean_pipeline_data(db)
    
    if result["status"] == "success":
        await log_action(
            db,
            user_id=current_user.id,
            action="CLEAN_PIPELINE",
            target="DATABASE",
            details=f"Total rows deleted: {result['total_deleted']}",
            ip_address=request.client.host if request.client else None
        )
        return {"status": "success", "message": f"Successfully cleaned {result['total_deleted']} rows from the pipeline tables."}
    else:
        raise HTTPException(status_code=500, detail=result["message"])

@router.post("/jobs/trigger/{job_name}")
@router.post("/jobs/trigger/{job_name}")
async def trigger_job(
    job_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    from app.utils.jobs import create_job_record
    
    """Manually trigger a background job."""
    task_map = {
        "fetch": tasks.fetch_articles_job,
        "normalize": tasks.normalize_articles_job,
        "cluster": tasks.clustering_job,
        "trends": tasks.trend_update_job,
        "ai": tasks.ai_analysis_job,
        "video": tasks.video_fetch_job,
    }
    
    job_type_map = {
        "fetch": "FETCH_ARTICLES",
        "normalize": "NORMALIZE_ARTICLES",
        "cluster": "CLUSTERING",
        "trends": "TREND_UPDATE",
        "ai": "AI_ANALYSIS",
        "video": "VIDEO_FETCH",
    }
    
    if job_name not in task_map:
        raise HTTPException(status_code=400, detail=f"Job {job_name} not found")
    
    # 1. Create Job Record Immediately (PENDING)
    job_type = job_type_map.get(job_name, "UNKNOWN")
    job_id = await create_job_record(db, job_type)
    
    # 2. Dispatch Task with job_id
    # Note: We pass job_id as argument to the task
    task = task_map[job_name].delay(job_id=job_id)
    
    # Store Celery Task ID in payload for cancellation
    from app.utils.jobs import update_job_status
    if not job_id: # Should not happen based on create_job_record above
        pass 
        
    # We need to update the job with the task_id. 
    # create_job_record creates the job. We now need to append to payload.
    # Since payload is JSON, we fetch, update, save.
    
    # Re-fetch job to update payload
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if job:
        payload = dict(job.payload) if job.payload else {}
        payload["celery_task_id"] = task.id
        job.payload = payload
        await db.commit()

    # 3. Log the action
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="TRIGGER_JOB",
        target=f"JOB:{job_type}",
        details=f"Job ID: {job_id}, Task ID: {task.id}",
        ip_address=request.client.host if request.client else None
    )
    
    if "application/json" in request.headers.get("accept", ""):
        return {"status": "queued", "job_id": job_id, "job_name": job_name, "task_id": task.id}

    return RedirectResponse(url="/admin/jobs-ui", status_code=303)

@router.get("/jobs/list")
async def get_jobs_api(
    request: Request,
    page: int = 1,
    limit: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """API endpoint to get recent jobs as JSON with pagination."""
    offset = (page - 1) * limit
    try:
        # Sort by started_at desc, but fall back to id if started_at is none (pending jobs)
        result = await db.execute(
            select(Job)
            .order_by(Job.started_at.desc().nulls_first(), Job.id.desc())
            .offset(offset)
            .limit(limit)
        )
        jobs = result.scalars().all()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Cancel a running background job."""
    from app.utils.jobs import update_job_status
    
    # 1. Fetch Job
    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in ["PENDING", "RUNNING", "STARTED"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in {job.status} state")
        
    # 2. Get Celery Task ID
    celery_task_id = None
    if job.payload and "celery_task_id" in job.payload:
        celery_task_id = job.payload["celery_task_id"]
        
    if celery_task_id:
        # Revoke the task
        celery_app.control.revoke(celery_task_id, terminate=True)
        # Verify? No easy way to verify immediately without checking celery events
    
    # 3. Update Job Status
    await update_job_status(db, job_id, "CANCELLED", error="Cancelled by user")
    
    # Audit
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="CANCEL_JOB",
        target=f"JOB:{job.type}",
        details=f"Job ID: {job_id}",
        ip_address=request.client.host if request.client else None
    )
    
    return {"status": "cancelled", "job_id": job_id}

@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Retry a failed or cancelled job."""
    from app.workers import tasks
    from app.utils.jobs import create_job_record
    
    # 1. Fetch Original Job
    res = await db.execute(select(Job).where(Job.id == job_id))
    old_job = res.scalar_one_or_none()
    
    if not old_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Map job type to task function
    # In trigger_job we use a map. We should extract that map to a shared location or duplicate it.
    # Duplicating for now for simplicity, or we can inspect the type.
    
    task_map = {
        "FETCH_ARTICLES": tasks.fetch_articles_job,
        "NORMALIZE_ARTICLES": tasks.normalize_articles_job,
        "CLUSTERING": tasks.clustering_job,
        "TREND_UPDATE": tasks.trend_update_job,
        "AI_ANALYSIS": tasks.ai_analysis_job,
        "VIDEO_FETCH": tasks.video_fetch_job,
    }
    
    if old_job.type not in task_map:
        raise HTTPException(status_code=400, detail=f"Cannot retry job type {old_job.type}")
        
    # 2. Create NEW Job Record
    # We use the same payload as args if possible, but our current tasks mostly use payload for context
    # or specific args. `create_job_record` takes payload.
    
    new_job_id = await create_job_record(db, old_job.type, payload=old_job.payload)
    
    # 3. Dispatch
    # We need to consider how tasks are called. 
    # tasks.fetch_articles_job.delay(job_id=new_job_id)
    # Most tasks take job_id and maybe other args.
    # We should inspect old_job.payload for specific args if relevant.
    
    # Special handling for VIDEO_FETCH and AI_ANALYSIS which might have topic_id
    kwargs = {"job_id": new_job_id}
    if old_job.payload:
        if "topic_id" in old_job.payload:
            kwargs["topic_id"] = old_job.payload["topic_id"]
            
    task = task_map[old_job.type].delay(**kwargs)
    
    # Update new job with task id
    # Re-fetch to update payload
    res = await db.execute(select(Job).where(Job.id == new_job_id))
    new_job = res.scalar_one()
    if new_job:
        payload = dict(new_job.payload) if new_job.payload else {}
        payload["celery_task_id"] = task.id
        new_job.payload = payload
        await db.commit()
    
    # Audit
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="RETRY_JOB",
        target=f"JOB:{old_job.type}",
        details=f"Retried Job {job_id} -> New Job {new_job_id}",
        ip_address=request.client.host if request.client else None
    )
    
    return {"status": "retried", "original_job_id": job_id, "new_job_id": new_job_id}

@router.post("/sources/{source_id}/edit")
async def edit_source(
    source_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    from app.models.source import SourceType, SourceCategory
    
    # Fetch source
    res = await db.execute(select(Source).where(Source.id == source_id))
    source = res.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    form = await request.form()
    name = form.get("name")
    url = form.get("url")
    domain = form.get("domain")
    source_type_str = form.get("type", "website")
    category_str = form.get("category", "general")
    api_key = form.get("api_key")
    if not api_key: # Handle empty string or None
        api_key = None
        
    reliability = float(form.get("reliability_score", 0.0))
    bias = float(form.get("bias_rating", 0.0))
    is_active = form.get("is_active") == "on"

    # Map Enums
    try:
        source_type = SourceType(source_type_str)
    except ValueError:
        source_type = SourceType.WEBSITE

    try:
        category = SourceCategory(category_str)
    except ValueError:
        category = SourceCategory.GENERAL
    
    # Update fields
    source.name = name
    source.url = url
    source.domain = domain
    source.type = source_type
    source.category = category
    source.api_key = api_key
    source.reliability_score = reliability
    source.bias_rating = bias
    source.is_active = is_active
    
    await db.commit()
    await db.refresh(source)
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="UPDATE_SOURCE",
        target=f"SOURCE:{source.name}",
        details=f"ID: {source.id}, Changes applied",
        ip_address=request.client.host if request.client else None
    )
    
    return RedirectResponse(url="/admin/sources-ui", status_code=303)

@router.post("/sources/{source_id}/delete")
async def delete_source(
    source_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    
    res = await db.execute(select(Source).where(Source.id == source_id))
    source = res.scalar_one_or_none()
    
    if source:
        await db.delete(source)
        await db.commit()
        
        # Audit Log
        from app.services.audit_service import log_action
        await log_action(
            db,
            user_id=current_user.id,
            action="DELETE_SOURCE",
            target=f"SOURCE:{source.name}",
            details=f"ID: {source_id}",
            ip_address=request.client.host if request.client else None
        )
        
    return RedirectResponse(url="/admin/sources-ui", status_code=303)
@router.get("/jobs/status/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Check the database status of a background job."""
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job record not found")
    
    return job

# --- Settings & Governance ---

@router.get("/settings/ai-providers", response_model=List[AIProviderSchema])
async def get_ai_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
    return result.scalars().all()

@router.post("/settings/ai-providers", response_model=AIProviderSchema)
async def create_or_update_ai_provider(provider_data: AIProviderCreate, db: AsyncSession = Depends(get_db)):
    # Simple upsert logic
    result = await db.execute(select(AIProvider).where(AIProvider.name == provider_data.name))
    provider = result.scalar_one_or_none()
    
    if provider:
        for key, value in provider_data.model_dump().items():
            setattr(provider, key, value)
    else:
        provider = AIProvider(**provider_data.model_dump())
        db.add(provider)
    
    await db.commit()
    await db.refresh(provider)
    return provider

@router.post("/settings/ai-providers/{provider_name}/verify")
async def verify_ai_provider(
    provider_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Verify if AI provider is working and has tokens."""
    result = await db.execute(select(AIProvider).where(AIProvider.name == provider_name))
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    status = "unknown"
    error_msg = None
    
    try:
        if provider.name.lower() in ["gemini", "google"]:
            from app.services.ai.gemini_service import GeminiService
            service = GeminiService()
            # Simple test call
            await asyncio.to_thread(service.generate_content, "Hello", model=provider.model, max_tokens=5)
            status = "active"
        elif provider.name.lower() in ["claude", "anthropic"]:
            from app.services.ai.claude_service import ClaudeService
            service = ClaudeService(api_key=provider.api_key)
            # Use 'claude-3-haiku-20240307' for lightweight health checks if possible
            # but default to the provider's configured model for absolute verification
            await asyncio.to_thread(service.generate_content, "Hi", model=provider.model, max_tokens=10)
            status = "active"
        elif provider.name.lower() == "openai":
            from app.services.ai.openai_service import OpenAIService
            service = OpenAIService(api_key=provider.api_key)
            await asyncio.to_thread(service.generate_content, "Hello", model=provider.model, max_tokens=5)
            status = "active"
        elif provider.name.lower() == "ollama":
            from app.services.ai.ollama_service import ollama_service
            if ollama_service.is_available():
                status = "active"
            else:
                status = "error"
                error_msg = "Ollama not reachable"
        else:
            status = "active" # Assume active if unknown type but configured? 
            
    except Exception as e:
        status = "error"
        error_msg = str(e)
        
    provider.status = status
    provider.last_checked = datetime.datetime.utcnow()
    await db.commit()
    
    return {"status": status, "error": error_msg, "last_checked": provider.last_checked}

@router.post("/settings/ai-providers/update")
async def update_ai_provider(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    
    form = await request.form()
    original_name = form.get("original_name")
    name = form.get("name") # Should be same as original_name usually, but if we allow rename we need check. 
    # For now, we rely on original_name to find the record.
    
    model = form.get("model")
    api_url = form.get("api_url")
    api_key = form.get("api_key")
    priority = int(form.get("priority", 0))
    daily_budget = float(form.get("daily_budget_usd", 5.0))
    
    result = await db.execute(select(AIProvider).where(AIProvider.name == original_name))
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider.model = model
    provider.priority = priority
    provider.daily_budget_usd = daily_budget
    if api_url:
        provider.api_url = api_url
    else:
        provider.api_url = None # or empty string?
        
    if api_key and api_key.strip():
        provider.api_key = api_key
        
    await db.commit()
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="UPDATE_AI_PROVIDER",
        target=f"AI_PROVIDER:{name}",
        details=f"Model: {model}",
        ip_address=request.client.host if request.client else None
    )
    
    return RedirectResponse(url="/admin/settings", status_code=303)

@router.post("/settings/ai-toggle")
async def toggle_ai_provider(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    form = await request.form()
    name = form.get("name")
    enabled = form.get("enabled").lower() == "true"
    
    result = await db.execute(select(AIProvider).where(AIProvider.name == name))
    provider = result.scalar_one_or_none()
    
    if provider:
        provider.enabled = enabled
        await db.commit()
        
        # Audit Log
        from app.services.audit_service import log_action
        await log_action(
            db,
            user_id=current_user.id,
            action="TOGGLE_AI_PROVIDER",
            target=f"AI_PROVIDER:{name}",
            details=f"Enabled: {enabled}",
            ip_address=request.client.host if request.client else None
        )
    
    return RedirectResponse(url="/admin/settings", status_code=303)

@router.get("/settings/feature-flags", response_model=List[FeatureFlagSchema])
async def get_feature_flags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureFlag))
    return result.scalars().all()

@router.post("/settings/feature-flags")
async def update_feature_flag(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    # Handle both JSON and Form data
    if "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
        key = data.get("key")
        enabled = data.get("enabled")
    else:
        form = await request.form()
        key = form.get("key")
        enabled = form.get("enabled").lower() == "true"
    
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = result.scalar_one_or_none()
    
    if not flag:
        flag = FeatureFlag(key=key, enabled=enabled)
        db.add(flag)
    else:
        flag.enabled = enabled
    
    await db.commit()
    await db.refresh(flag)
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db, 
        user_id=current_user.id,
        action="UPDATE_FEATURE_FLAG",
        target=f"FEATURE_FLAG:{key}",
        details=f"Enabled: {enabled}",
        ip_address=request.client.host if request.client else None
    )
    
    # If it was a form post, redirect back to settings
    if "application/json" not in request.headers.get("content-type", ""):
        return RedirectResponse(url="/admin/settings", status_code=303)
        
    return flag

@router.get("/dashboard/health", response_model=List[SourceHealthSchema])
async def get_source_health(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceHealth))
    return result.scalars().all()

# --- Source Management ---

@router.post("/sources")
async def create_source(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    from app.models.source import SourceType, SourceCategory
    
    form = await request.form()
    name = form.get("name")
    url = form.get("url")
    domain = form.get("domain")
    source_type_str = form.get("type", "website")
    category_str = form.get("category", "general")
    api_key = form.get("api_key")
    if not api_key:
        api_key = None # ensure it's None if empty string
        
    reliability = float(form.get("reliability_score", 0.0))
    bias = float(form.get("bias_rating", 0.0))
    
    # Check if exists
    res = await db.execute(select(Source).where(Source.name == name))
    if res.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Source already exists")
    
    # Map string to Enum (safer way)
    try:
        source_type = SourceType(source_type_str)
    except ValueError:
        source_type = SourceType.WEBSITE

    try:
        category = SourceCategory(category_str)
    except ValueError:
        category = SourceCategory.GENERAL

    new_source = Source(
        name=name,
        url=url,
        domain=domain,
        type=source_type,
        category=category,
        api_key=api_key,
        reliability_score=reliability,
        bias_rating=bias,
        is_active=True
    )
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="CREATE_SOURCE",
        target=f"SOURCE:{name}",
        details=f"Type: {source_type.value}, Category: {category.value}, Domain: {domain}",
        ip_address=request.client.host if request.client else None
    )
    
    return RedirectResponse(url="/admin/sources-ui", status_code=303)

@router.post("/sources/{source_id}/delete")
async def delete_source(
    source_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    
    res = await db.execute(select(Source).where(Source.id == source_id))
    source = res.scalar_one_or_none()
    
    if source:
        await db.delete(source)
        await db.commit()
        
        # Audit Log
        from app.services.audit_service import log_action
        await log_action(
            db,
            user_id=current_user.id,
            action="DELETE_SOURCE",
            target=f"SOURCE:{source.name}",
            details=f"ID: {source_id}",
            ip_address=request.client.host if request.client else None
        )
        
    return RedirectResponse(url="/admin/sources-ui", status_code=303)

# --- User Management ---

@router.post("/users")
async def create_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    from app.utils.security import get_password_hash
    
    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    full_name = form.get("full_name")
    is_superuser = form.get("is_superuser") == "true"
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=True,
        is_superuser=is_superuser
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="CREATE_USER",
        target=f"USER:{email}",
        details=f"Superuser: {is_superuser}",
        ip_address=request.client.host if request.client else None
    )
    
    return RedirectResponse(url="/admin/users-ui", status_code=303)

@router.post("/users/{user_id}/role")
async def toggle_user_role(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    
    form = await request.form()
    is_superuser = form.get("is_superuser") == "true"
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_superuser = is_superuser
    await db.commit()
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="UPDATE_USER_ROLE",
        target=f"USER:{user.email}",
        details=f"Superuser: {is_superuser}",
        ip_address=request.client.host if request.client else None
    )
    
    return RedirectResponse(url="/admin/users-ui", status_code=303)

    return RedirectResponse(url="/admin/users-ui", status_code=303)

@router.get("/logs/export")
async def export_logs_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import StreamingResponse
    from app.models.audit import AuditLog
    from sqlalchemy import select
    import csv
    import io
    
    # Fetch recent logs for export
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5000))
    logs = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Action', 'Target', 'Details', 'User ID', 'IP Address', 'Created At'])
    
    for log in logs:
        writer.writerow([
            log.id, 
            log.action, 
            log.target, 
            log.details, 
            log.user_id, 
            log.ip_address, 
            log.created_at.isoformat() if log.created_at else ''
        ])
    
    output.seek(0)
    
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=audit_logs.csv"
    return response

@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    from fastapi.responses import RedirectResponse
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = not user.is_active
    await db.commit()
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="TOGGLE_USER_ACTIVE",
        target=f"USER:{user.email}",
        details=f"Active: {user.is_active}",
        ip_address=request.client.host if request.client else None
    )
    
    return RedirectResponse(url="/admin/users-ui", status_code=303)

@router.get("/agents/status")
async def get_agents_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Get the pause status of all AI agents."""
    agents = ["intelligence", "completeness", "category"]
    status = {}
    
    for agent in agents:
        key = f"agent_{agent}_paused"
        res = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        flag = res.scalar_one_or_none()
        status[agent] = "paused" if (flag and flag.enabled) else "active"
        
    return status

@router.post("/agents/toggle")
async def toggle_agent(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Toggle the pause status of an AI agent."""
    data = await request.json()
    agent = data.get("agent") # intelligence, completeness, category
    
    if agent not in ["intelligence", "completeness", "category"]:
        raise HTTPException(status_code=400, detail="Invalid agent name")
        
    key = f"agent_{agent}_paused"
    res = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = res.scalar_one_or_none()
    
    if not flag:
        flag = FeatureFlag(key=key, enabled=True)
        db.add(flag)
    else:
        flag.enabled = not flag.enabled
        
    await db.commit()
    await db.refresh(flag)
    
    # Audit Log
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=current_user.id,
        action="TOGGLE_AGENT",
        target=f"AGENT:{agent.upper()}",
        details=f"Paused: {flag.enabled}",
        ip_address=request.client.host if request.client else None
    )
    
    return {"agent": agent, "status": "paused" if flag.enabled else "active"}
