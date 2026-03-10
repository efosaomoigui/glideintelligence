import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Source, RawArticle
from app.services.crawler_service import CrawlerService

async def verify_crawler():
    print(f"Connecting to DB: {settings.DATABASE_URL}...")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get a source
        source = (await session.execute(select(Source).limit(1))).scalar_one_or_none()
        if not source:
            print("No sources found! Run seed_sources.py first.")
            return

        print(f"Testing CrawlerService with source: {source.name} ({source.url})")
        crawler = CrawlerService(session)
        
        try:
            count = await crawler.fetch_articles(source)
            print(f"Successfully fetched {count} articles.")
        except Exception as e:
            print(f"Error fetching articles: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_crawler())
