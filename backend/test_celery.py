import asyncio
import sys
from app.workers.tasks import fetch_articles_job
from app.database import AsyncSessionLocal
from app.models import Job
from app.workers.celery_app import celery_app

# Let's see if we can trigger the job in Celery via python

async def main():
    print("Testing triggering job via background worker.")
    # just create a fake job
    job_id = "test-job-id"
    # Try calling delay
    task = fetch_articles_job.delay(job_id=job_id)
    print(f"Task triggered: {task.id}")
    
    # Wait for result
    res = task.get(timeout=30)
    print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(main())
