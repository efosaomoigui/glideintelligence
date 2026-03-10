import sys
import os
import asyncio
from app.workers.tasks import fetch_articles_job, normalize_articles_job, clustering_job, ai_analysis_job
from app.utils.jobs import create_job_record, update_job_status
from app.database import AsyncSessionLocal
from app.models import Job
from sqlalchemy import select

async def run_task(task_func, job_type):
    async with AsyncSessionLocal() as db:
        job_id = await create_job_record(db, job_type)
        print(f"Triggering {job_type} (Job ID: {job_id})...")
        
        # Call the task with job_id
        task_func.delay(job_id=job_id)
        
        print(f"Monitoring {job_id}...")
        while True:
            await asyncio.sleep(5)
            # Re-fetch job to check status
            # Create a new session for each check to avoid stale cache
            async with AsyncSessionLocal() as db_check:
                res = await db_check.execute(select(Job).where(Job.id == job_id))
                job = res.scalar_one_or_none()
                if not job:
                    print("Job record missing!")
                    break
                
                print(f"   [{job_type}] Status: {job.status}")
                if job.status == "COMPLETED":
                    print(f"FINISHED: {job_type} COMPLETED!")
                    return True
                elif job.status == "FAILED":
                    print(f"FAILED: {job_type} FAILED! Error: {job.error}")
                    return False
                elif job.status == "CANCELLED":
                    print(f"CANCELLED: {job_type} CANCELLED.")
                    return False

if __name__ == "__main__":
    import os
    # Add project root to path
    sys.path.append(os.getcwd())
    
    task_name = sys.argv[1]
    
    tasks = {
        "fetch": (fetch_articles_job, "FETCH_ARTICLES"),
        "normalize": (normalize_articles_job, "NORMALIZE_ARTICLES"),
        "cluster": (clustering_job, "CLUSTERING"),
        "ai": (ai_analysis_job, "AI_ANALYSIS")
    }
    
    if task_name not in tasks:
        print(f"Unknown task. Choice: {list(tasks.keys())}")
        sys.exit(1)
        
    func, jtype = tasks[task_name]
    asyncio.run(run_task(func, jtype))
