import asyncio
import os
import sys
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.topic import Topic

async def list_latest_titles():
    async with AsyncSessionLocal() as db:
        query = select(Topic.title).order_by(Topic.created_at.desc()).limit(15)
        result = await db.execute(query)
        titles = result.scalars().all()
        
        print("\n--- LATEST TOPIC TITLES ---")
        for i, title in enumerate(titles, 1):
            # Strip non-ascii for terminal safety
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"{i}. {safe_title}")
        print("---------------------------\n")

if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    asyncio.run(list_latest_titles())
