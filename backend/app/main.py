from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config import settings
from app.database import get_db
from app.workers.celery_app import celery_app
import redis.asyncio as redis

from app.routes import public, admin, admin_ui, auth, interactions, intelligence, ads
from prometheus_fastapi_instrumentator import Instrumentator

# Setup logging
from app.utils.logging_config import setup_logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG
)

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(admin_ui.router)
app.include_router(interactions.router)
app.include_router(intelligence.router)
app.include_router(ads.router)

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown"
    }

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await r.ping()
        await r.close()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        
    # Check Celery (Basic check if app is configured)
    if celery_app:
        health_status["celery"] = "configured"

    return health_status

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin")
