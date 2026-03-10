import sys
import os
import asyncio
import time
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import select, desc, func
from app.database import AsyncSessionLocal
from app.models import Job, Source, RawArticle, Topic, TopicAnalysis
from app.workers.tasks import (
    fetch_articles_job, 
    normalize_articles_job, 
    clustering_job, 
    ai_analysis_job
)

# Helper config
POLL_INTERVAL = 2
TIMEOUT = 60 * 5 # 5 mins max per step

async def wait_for_celery_result(task_result):
    """Wait for Celery task to finish and return its result."""
    # Note: In a real script with a worker, we rely on the backend.
    # Here we might need to just poll the DB if we can't access Redis easily from this script context 
    # or if we want to be backend-agnostic.
    # BUT, our tasks return a DB Job ID or a status dict.
    
    # Simpler approach: The tasks are triggering logic that updates the 'jobs' table (mostly).
    # fetch_articles_job returns {"job_id": ...}
    
    # We will assume the worker is running and processing.
    # We'll just sleep a bit for the task to be picked up.
    print("Waiting for worker to pick up task...")
    start = time.time()
    while not task_result.ready():
        if time.time() - start > 300: # Increased timeout
            print("Timeout waiting for Celery task to be ready.")
            return None
        await asyncio.sleep(1)
    
    return task_result.get()

async def wait_for_db_job(job_id):
    """Poll DB for Job status."""
    print(f"Polling DB for Job {job_id}...")
    start = time.time()
    async with AsyncSessionLocal() as db:
        while time.time() - start < TIMEOUT:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                print("Job record not found yet...")
            elif job.status in ["COMPLETED", "SUCCESS"]:
                print(f"Job {job_id} COMPLETED. Result: {job.result}")
                return True
            elif job.status in ["FAILED", "FAILURE"]:
                print(f"Job {job_id} FAILED. Error: {job.error}")
                return False
            else:
                # print(f"Job {job_id} is {job.status}...")
                pass
            
            await asyncio.sleep(POLL_INTERVAL)
    
    print(f"Timeout waiting for Job {job_id}")
    return False

async def get_counts(label):
    async with AsyncSessionLocal() as db:
        s_count = (await db.execute(select(func.count(Source.id)).where(Source.is_active==True))).scalar()
        a_count = (await db.execute(select(func.count(RawArticle.id)))).scalar()
        t_count = (await db.execute(select(func.count(Topic.id)))).scalar()
        ta_count = (await db.execute(select(func.count(TopicAnalysis.id)))).scalar()
        
        print(f"--- STATS [{label}] ---")
        print(f"Active Sources: {s_count}")
        print(f"Articles: {a_count}")
        print(f"Topics: {t_count}")
        print(f"Analyses: {ta_count}")
        print("-----------------------")

async def run_pipeline():
    print("=== STARTING FULL PIPELINE TEST ===")
    
    # 0. Initial Stats
    await get_counts("INITIAL")

    # 1. Ingestion
    print("\n[STEP 1] Triggering INGESTION...")
    task = fetch_articles_job.delay()
    result = await wait_for_celery_result(task)
    
    if result and isinstance(result, dict) and "job_id" in result:
        job_id = result["job_id"]
        # In fetch_articles_job, it returns a coroutine object if not awaited properly in celery?
        # Wait, tasks.py definition: 
        #   job_id = run_async(_run())
        #   return {"status": "success", "job_id": job_id}
        # It calls run_async, which runs the loop. So it should return the ID.
        success = await wait_for_db_job(job_id)
        if not success:
            print("Ingestion failed in DB job.")
            return
    else:
        # Some tasks might not create a DB job or return differently.
        print(f"Ingestion task returned: {result}")
        if result == 0: # Feature flag overlap?
             pass 

    await get_counts("AFTER INGESTION")

    # 2. Normalization
    print("\n[STEP 2] Triggering NORMALIZATION...")
    task = normalize_articles_job.delay()
    # normalization returns {"normalized_count": ...} directly, it does NOT create a 'jobs' record in the current code (tasks.py lines 80+).
    # Wait, looking at tasks.py: normalize_articles_job DOES NOT call create_job_record. 
    # It just runs and returns a dict.
    res = await wait_for_celery_result(task)
    print(f"Normalization Result: {res}")
    
    await get_counts("AFTER NORMALIZATION")

    # 3. Clustering
    print("\n[STEP 3] Triggering CLUSTERING...")
    task = clustering_job.delay()
    # Also just returns dict
    res = await wait_for_celery_result(task)
    print(f"Clustering Result: {res}")
    
    await get_counts("AFTER CLUSTERING")

    # 4. Analysis
    print("\n[STEP 4] Triggering AI ANALYSIS...")
    task = ai_analysis_job.delay()
    # Also just returns dict
    res = await wait_for_celery_result(task)
    print(f"Analysis Result: {res}")

    await get_counts("FINAL")
    print("\n=== PIPELINE TEST COMPLETE ===")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_pipeline())
