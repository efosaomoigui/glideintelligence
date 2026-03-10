import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.job import Job

async def check_job_result():
    job_id = "b7107b5a-bdfe-47f3-9ba6-e0fa9cfaefc6"
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job:
            print(f"Job ID: {job.id}")
            print(f"Status: {job.status}")
            print(f"Result: {job.result}")
            print(f"Error: {job.error}")
        else:
            print("Job not found")

if __name__ == "__main__":
    asyncio.run(check_job_result())
