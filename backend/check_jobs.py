import asyncio
from app.database import AsyncSessionLocal
from app.models import Job
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Job).order_by(Job.id.desc()).limit(10))
        jobs = res.scalars().all()
        for j in jobs:
            print(f"[{j.id}] Type: {j.type} | Status: {j.status} | Started: {j.started_at} | Error: {j.error}")

if __name__ == "__main__":
    asyncio.run(main())
