import asyncio
from app.database import AsyncSessionLocal
from app.models import Job
from sqlalchemy import select, desc
import json

async def check_recent_jobs():
    async with AsyncSessionLocal() as db:
        query = select(Job).order_by(desc(Job.created_at)).limit(5)
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        print(f"\n--- RECENT JOBS ---")
        for j in jobs:
            print(f"ID: {j.id}")
            print(f"Type: {j.type}")
            print(f"Status: {j.status}")
            print(f"Created: {j.created_at}")
            print(f"Started: {j.started_at}")
            print(f"Completed: {j.completed_at}")
            print(f"Error: {j.error}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_recent_jobs())
