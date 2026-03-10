import asyncio
from app.database import AsyncSessionLocal
from app.models import Topic
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Topic).where(Topic.status == 'analysis_failed'))
        topics = res.scalars().all()
        for t in topics:
            print(f"Topic {t.id} ({t.title}):")
            if t.metadata_:
                print(f"  Error: {t.metadata_.get('last_error')}")

if __name__ == "__main__":
    asyncio.run(main())
