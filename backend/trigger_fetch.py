import sys
import os
sys.path.append(os.getcwd())
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"
from app.workers.tasks import fetch_articles_job

if __name__ == "__main__":
    print("Triggering fetch_articles_job...")
    result = fetch_articles_job.delay()
    print(f"Job triggered via Celery: {result.id}")
