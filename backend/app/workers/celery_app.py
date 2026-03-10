from celery import Celery
from app.config import settings

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Beat Schedule
    beat_schedule={
        "fetch-articles-every-4-hours": {
            "task": "fetch_articles_job",
            "schedule": 14400.0, # 4 hours
        },
        "update-trends-every-hour": {
            "task": "trend_update_job",
            "schedule": 3600.0, # 1 hour
        },
    }
)

# Auto-discover tasks from the workers package
celery_app.autodiscover_tasks(["app.workers"])
