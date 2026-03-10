import asyncio
from app.database import AsyncSessionLocal
from app.models import Job
from sqlalchemy import select, desc

async def list_all_ai_jobs():
    async with AsyncSessionLocal() as db:
        query = select(Job).where(Job.type == "AI_ANALYSIS").order_by(desc(Job.created_at))
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        print(f"\n--- ALL AI ANALYSIS JOBS ({len(jobs)}) ---")
        for j in jobs:
            print(f"ID: {j.id} | Status: {j.status} | Created: {j.created_at}")
            if j.error:
                print(f"  Error: {j.error[:100]}...")

if __name__ == "__main__":
    asyncio.run(list_all_ai_jobs())
