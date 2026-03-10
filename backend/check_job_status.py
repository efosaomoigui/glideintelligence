import asyncio
from app.database import AsyncSessionLocal
from app.models import Job
from sqlalchemy import select

async def check_specific_job(job_id: str):
    async with AsyncSessionLocal() as db:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if job:
            print(f"ID: {job.id}")
            print(f"Status: {job.status}")
            print(f"Started: {job.started_at}")
            print(f"Completed: {job.completed_at}")
            print(f"Error: {job.error}")
        else:
            print(f"Job {job_id} not found.")

if __name__ == "__main__":
    import sys
    job_id = "5072eb1b-c727-479d-9d39-fe8b7e340bf9"
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
    asyncio.run(check_specific_job(job_id))
