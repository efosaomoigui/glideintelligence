import asyncio
from sqlalchemy import select, func, or_
from app.database import AsyncSessionLocal
from app.models.job import Job
from app.models.topic import TopicArticle

async def check_pending_and_topics():
    async with AsyncSessionLocal() as db:
        # Check stuck jobs
        print("--- Stuck/Pending Jobs ---")
        result = await db.execute(select(Job).where(or_(Job.status == "PENDING", Job.status == "RUNNING")))
        jobs = result.scalars().all()
        if not jobs:
            print("No pending or running jobs found.")
        else:
            for job in jobs:
                print(f"ID: {job.id} | Type: {job.type} | Status: {job.status} | Created: {job.created_at}")

        # Check Topic Associations
        print("\n--- Topic Associations ---")
        result = await db.execute(select(func.count(TopicArticle.id)))
        count = result.scalar()
        print(f"Topic-Article Assignments: {count}")

if __name__ == "__main__":
    asyncio.run(check_pending_and_topics())
