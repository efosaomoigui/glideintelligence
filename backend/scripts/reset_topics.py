import asyncio
import logging
import sys
import os

# Add the parent directory to sys.path to find 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.topic import Topic
from sqlalchemy import update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_processing_topics():
    """Reset all topics stuck in 'processing' back to 'pending'."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Resetting topics stuck in 'processing' status...")
            result = await session.execute(
                update(Topic)
                .where(Topic.analysis_status.in_(["processing", "failed", "pipeline_failed"]))
                .values(analysis_status='pending')
            )
            await session.commit()
            logger.info(f"Successfully reset {result.rowcount} topics.")
        except Exception as e:
            logger.error(f"Failed to reset topics: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(reset_processing_topics())
