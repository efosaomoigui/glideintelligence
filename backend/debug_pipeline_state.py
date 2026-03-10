import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import ArticleEmbedding, Job, RawArticle

async def debug_state():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check Embeddings
        embedding_count = (await session.execute(select(func.count(ArticleEmbedding.id)))).scalar()
        print(f"Article Embeddings: {embedding_count}")
        
        # Check Recent Jobs
        print("\nRecent Jobs:")
        jobs = (await session.execute(select(Job).order_by(desc(Job.created_at)).limit(10))).scalars().all()
        for job in jobs:
            print(f"- {job.type} [{job.status}] ID: {job.id} Started: {job.started_at}")
            print(f"  Result: {job.result}")
            if job.error:
                print(f"  Error: {job.error}")

        # Check Feature Flags
        print("\nFeature Flags:")
        from app.models.settings import FeatureFlag
        flags = (await session.execute(select(FeatureFlag))).scalars().all()
        for f in flags:
            print(f"- {f.key}: {f.enabled}")
        if not flags:
            print("No feature flags found (Defaults to True).")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_state())
