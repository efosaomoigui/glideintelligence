import sys
import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Load .env from backend dir
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.workers.tasks import fetch_articles_job

# Sync DB connection for monitoring (to avoid async loop issues with the task wrapper)
DATABASE_URL = os.environ.get("DATABASE_URL")
# Adjust for sync driver if needed, usually asyncpg is in URL. 
# We'll need a sync monitoring or just use a separate async loop logic CAREFULLY.
# Actually, calling fetch_articles_job.apply() might verify the logic, but it's cleaner to separate TRIGGER and MONITOR.

def monitor_pipeline_sync():
    print("=== PIPELINE MONITOR (SYNC) ===")
    
    # 1. Trigger Job Synchronously
    print("Triggering 'fetch_articles_job' via apply()...")
    try:
        # This will run the logic in the current thread. 
        # The task uses run_async internally, ensuring it creates a loop if none exists.
        result = fetch_articles_job.apply(throw=True)
        print(f"Task finished. Result: {result.result}")
    except Exception as e:
        print(f"Task execution failed: {e}")

    # 2. Check DB
    # We'll use a simple sync engine (psycopg2) or just re-use the async one in a fresh loop? 
    # Let's try running a SEPARATE async loop for checking the DB *after* the task is done.
    
    import asyncio
    from sqlalchemy import select, desc
    from app.database import AsyncSessionLocal
    from app.models.job import Job

    async def check_db():
        print("\nChecking Jobs Table...")
        # Create a fresh engine/session for this check to avoid any loop/connection binding issues from previous calls if any
        from app.database import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Job).order_by(desc(Job.created_at)).limit(1))
                job = res.scalar_one_or_none()
                
                if job:
                    print(f"Latest Job ID: {job.id}")
                    print(f"Status: {job.status}")
                    print(f"Result: {job.result}")
                    print(f"Error: {job.error}")
                else:
                    print("No job found.")
        except Exception as e:
            print(f"Error checking DB: {e}")

    try:
        asyncio.run(check_db())
    except Exception as e:
        print(f"Asyncio run failed: {e}")

if __name__ == "__main__":
    monitor_pipeline_sync()
