import asyncio
from app.database import AsyncSessionLocal
from app.models.topic import Topic
from sqlalchemy import select

async def get_slug():
    async with AsyncSessionLocal() as db:
        topic = (await db.execute(select(Topic).filter(Topic.id == 373))).scalar_one_or_none()
        print(topic.slug if topic else 'not found')

if __name__ == "__main__":
    asyncio.run(get_slug())
