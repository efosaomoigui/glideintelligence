import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.job import Job

async def check_specific_jobs():
    async with AsyncSessionLocal() as db:
        print("--- Recent Normalization Jobs ---")
        result = await db.execute(select(Job).where(Job.type == "NORMALIZE_ARTICLES").order_by(Job.created_at.desc()).limit(3))
        jobs = result.scalars().all()
        for job in jobs:
            print(f"ID: {job.id} | Status: {job.status} | Created: {job.created_at}")

        print("\n--- Recent Clustering Jobs ---")
        result = await db.execute(select(Job).where(Job.type == "CLUSTERING").order_by(Job.created_at.desc()).limit(3))
        jobs = result.scalars().all()
        for job in jobs:
             print(f"ID: {job.id} | Status: {job.status} | Created: {job.created_at}")

if __name__ == "__main__":
    asyncio.run(check_specific_jobs())
