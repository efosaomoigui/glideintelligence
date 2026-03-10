import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(os.path.join(os.getcwd(), ".env"))

from app.database import AsyncSessionLocal
from sqlalchemy import select, desc
from app.models import Job

async def check_job():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).order_by(desc(Job.created_at)).limit(1))
        job = result.scalar_one_or_none()
        if job:
            print(f"Latest Job: ID={job.id}")
            print(f"Type: {job.type}")
            print(f"Status: {job.status}")
            print(f"Created: {job.created_at}")
            print(f"Updated: {job.updated_at}")
            if job.error:
                print(f"Error: {job.error}")
            if job.result:
                print(f"Result: {job.result}")
        else:
            print("No jobs found.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_job())
