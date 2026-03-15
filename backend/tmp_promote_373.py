import asyncio
from app.database import AsyncSessionLocal
from app.models.topic import Topic
from sqlalchemy import select, update

async def promote_373():
    async with AsyncSessionLocal() as db:
        # Update topic to be trending and featured
        await db.execute(
            update(Topic)
            .where(Topic.id == 373)
            .values(is_trending=True, is_featured=True, status='stable')
        )
        await db.commit()
        
        topic = (await db.execute(select(Topic).filter(Topic.id == 373))).scalar_one_or_none()
        if topic:
            print(f"Topic 373 updated: Trending={topic.is_trending}, Featured={topic.is_featured}, Slug={topic.slug}")
        else:
            print("Topic 373 not found")

if __name__ == "__main__":
    asyncio.run(promote_373())
