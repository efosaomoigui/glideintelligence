import asyncio
import logging
import os
import sys

# Configure logging to stdout so Docker can capture it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("openclaw_agents")

from sqlalchemy import select

# Import the centralized database dependencies
from app.database import AsyncSessionLocal
from app.models.topic import Topic
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob

async def process_next_topic(session: AsyncSessionLocal) -> bool:
    """
    Fetches the next available topic for intelligence enrichment.
    Uses FOR UPDATE SKIP LOCKED via GenerateTopicAnalysisJob.
    Returns True if a topic was processed, False otherwise.
    """
    try:
        # Find next pending topic
        query = (
            select(Topic.id)
            .where(Topic.analysis_status.in_(['pending', 'pipeline_failed']))
            .order_by(Topic.updated_at.desc())
            .limit(1)
        )
        
        result = await session.execute(query)
        topic_id = result.scalar_one_or_none()
        
        if not topic_id:
            logger.info("No pending topics found in database.")
            return False
            
        logger.info(f"OpenClaw Agent picking up topic {topic_id} for enrichment...")
        
        # Use the centralized job for full enrichment
        job = GenerateTopicAnalysisJob(session)
        await job.execute(topic_id)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in Agent topic handoff: {e}")
        return False

async def worker_loop():
    """Continuously poll the database for new topics."""
    logger.info("Starting OpenClaw Agent Service worker loop...")
    
    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Check for pause flag
                from app.models.settings import FeatureFlag
                res = await session.execute(select(FeatureFlag).where(FeatureFlag.key == "agent_intelligence_paused"))
                flag = res.scalar_one_or_none()
                if flag and flag.enabled:
                    logger.debug("Intelligence Agent is paused.")
                    processed_something = False
                    await asyncio.sleep(15)
                    continue

                processed_something = await process_next_topic(session)
                
            # If we found nothing, back off slightly to reduce DB polling spam
            if not processed_something:
                await asyncio.sleep(10)
            else:
                # tiny breather
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Critical error in worker loop: {e}")
            await asyncio.sleep(5)  # Backoff on error

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Shutting down OpenClaw Agent Service.")
