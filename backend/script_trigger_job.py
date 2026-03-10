import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv(os.path.join(os.getcwd(), ".env"))

from app.workers.tasks import fetch_articles_job

def trigger_job():
    print("Triggering fetch_articles_job...")
    try:
        # Use delay() to trigger via Celery
        result = fetch_articles_job.delay()
        print(f"Job triggered! Task ID: {result.id}")
        return result.id
    except Exception as e:
        print(f"Failed to trigger job: {e}")

from sqlalchemy import select, desc
from app.database import AsyncSessionLocal
from app.models import Job

async def check_job_db(task_id):
    print("Checking DB for job record...")
    await asyncio.sleep(2) # Wait for worker to pick up
    
    async with AsyncSessionLocal() as db:
        # Check for latest job
        query = select(Job).order_by(desc(Job.created_at)).limit(1)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if job:
            print(f"Found latest job: ID={job.id}, Type={job.type}, Status={job.status}")
            if job.status in ["COMPLETED", "SUCCESS"]:
                 print("Job completed successfully!")
            elif job.status in ["FAILED", "FAILURE"]:
                 print(f"Job failed: {job.error}")
            else:
                 print(f"Job is currently {job.status}. Waiting...")
                 # Could wait more or just report
        else:
            print("No job found in DB.")

if __name__ == "__main__":
    tid = trigger_job()
    if tid:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(check_job_db(tid))

