import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.job import Job
from app.services.ai.clustering_service import ClusteringService

async def debug_clustering():
    async with AsyncSessionLocal() as db:
        # 1. Check recent clustering jobs
        print("--- Recent Clustering Jobs ---")
        result = await db.execute(select(Job).where(Job.type == "CLUSTERING").order_by(Job.created_at.desc()).limit(5))
        jobs = result.scalars().all()
        for job in jobs:
            print(f"ID: {job.id} | Status: {job.status} | Error: {job.error}")

        # 2. Fix stuck jobs (older than 1 hour or just the specific one found)
        # The specific one found was ID: 64216848-dfad-48d2-8e14-753085d23a9c
        print("\n--- Fixing Stuck Jobs ---")
        stuck_id = "64216848-dfad-48d2-8e14-753085d23a9c"
        result = await db.execute(select(Job).where(Job.id == stuck_id))
        stuck_job = result.scalar_one_or_none()
        if stuck_job and stuck_job.status in ["PENDING", "RUNNING"]:
             stuck_job.status = "FAILED"
             stuck_job.error = "Manually marked as failed (stuck)"
             await db.commit()
             print(f"Marked job {stuck_id} as FAILED")
        else:
             print(f"Job {stuck_id} not found or not stuck")

if __name__ == "__main__":
    asyncio.run(debug_clustering())
