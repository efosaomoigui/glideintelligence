import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import RawArticle, ArticleEmbedding, Topic

async def check_status():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Total Articles
        total_articles = (await session.execute(select(func.count(RawArticle.id)))).scalar()
        
        # 2. Normalized Articles (using sentiment_score as proxy per tasks.py)
        normalized_articles = (await session.execute(select(func.count(RawArticle.id)).where(RawArticle.sentiment_score != None))).scalar()
        
        # 3. Embeddings
        embeddings = (await session.execute(select(func.count(ArticleEmbedding.id)))).scalar()
        
        # 4. Topics
        topics = (await session.execute(select(func.count(Topic.id)))).scalar()
        
        print("-" * 30)
        print(f"Total Articles:      {total_articles}")
        print(f"Normalized (Approx): {normalized_articles}")
        print(f"Embeddings:          {embeddings}")
        print(f"Topics:              {topics}")
        print("-" * 30)

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_status())
