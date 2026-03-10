import asyncio
from app.database import AsyncSessionLocal
from app.models import Job
from sqlalchemy import select, desc, func
from datetime import datetime, date

async def check_ai_jobs():
    async with AsyncSessionLocal() as db:
        today = date.today()
        query = select(Job).where(
            Job.type == "AI_ANALYSIS",
            func.date(Job.created_at) == today
        ).order_by(desc(Job.created_at))
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        print(f"\n--- AI ANALYSIS JOBS TODAY ({today}) ---")
        if not jobs:
            print("No AI_ANALYSIS jobs found for today.")
        for j in jobs:
            print(f"ID: {j.id}")
            print(f"Status: {j.status}")
            print(f"Created: {j.created_at}")
            print(f"Error: {j.error}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_ai_jobs())
