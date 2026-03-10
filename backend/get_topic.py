import os
import sys
import asyncio
from sqlalchemy import select

# Add backend to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models.topic import Topic

async def get_latest_topic():
    async with AsyncSessionLocal() as db:
        stmt = select(Topic).order_by(Topic.updated_at.desc()).limit(1)
        result = await db.execute(stmt)
        topic = result.scalar_one_or_none()
        if topic:
            print(f"ID: {topic.id}")
            print(f"Title: {topic.title}")
            print(f"Status: {topic.analysis_status}")
            slug = topic.title.lower().replace(' ', '-')
            print(f"Slug: {slug}")
        else:
            print("No topics found.")

if __name__ == "__main__":
    asyncio.run(get_latest_topic())
