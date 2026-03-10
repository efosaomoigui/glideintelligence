import asyncio
from app.database import AsyncSessionLocal
from app.models.job import Job
from sqlalchemy import select, desc
import sys

async def check_jobs():
    async with AsyncSessionLocal() as db:
        # Get active jobs
        query = select(Job).order_by(desc(Job.created_at)).limit(5)
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        print(f"\nLast 5 Jobs:")
        print("-" * 60)
        for job in jobs:
            print(f"ID: {job.id}")
            print(f"Type: {job.type}")
            print(f"Status: {job.status}")
            print(f"Created: {job.created_at}")
            print(f"Updated: {job.updated_at}")
            if job.error:
                print(f"Error: {job.error}")
            print("-" * 60)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_jobs())
