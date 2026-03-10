import asyncio
import logging
import sys
import os

# Add the current directory to sys.path to make app imports work
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.settings import FeatureFlag
from app.models.source import Source, SourceType, SourceCategory
from app.services.crawler_service import CrawlerService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_ingestion():
    logger.info("Starting Ingestion Debug Script...")
    
    async with AsyncSessionLocal() as db:
        # 1. Check Feature Flag
        logger.info("Checking 'CRAWLER' feature flag...")
        result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == "CRAWLER"))
        flag = result.scalar_one_or_none()
        
        if not flag:
            logger.info("Flag 'CRAWLER' not found. Creating and enabling it.")
            flag = FeatureFlag(key="CRAWLER", enabled=True)
            db.add(flag)
            await db.commit()
        elif not flag.enabled:
            logger.info("Flag 'CRAWLER' is disabled. Enabling it.")
            flag.enabled = True
            await db.commit()
        else:
            logger.info("Flag 'CRAWLER' is already enabled.")
            
        # 2. Check/Create Source
        source_name = "BBC Business"
        logger.info(f"Checking for source '{source_name}'...")
        result = await db.execute(select(Source).where(Source.name == source_name))
        source = result.scalar_one_or_none()
        
        if not source:
            logger.info(f"Source '{source_name}' not found. Creating it.")
            source = Source(
                name=source_name,
                url="http://feeds.bbci.co.uk/news/business/rss.xml",
                domain="bbc.com",
                type=SourceType.RSS,
                category=SourceCategory.FINANCIAL,
                is_active=True,
                reliability_score=0.9,
                bias_rating=0.0
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
        else:
             logger.info(f"Source '{source_name}' found. ID: {source.id}")
        
        # 3. Run Ingestion
        logger.info("Running ingestion for source...")
        crawler = CrawlerService(db)
        count = await crawler.fetch_articles(source)
        
        logger.info(f"Ingestion complete. Fetched {count} articles.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_ingestion())
