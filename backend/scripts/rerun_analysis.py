
import sys
import os
import asyncio
import logging

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Re-Analysis")

from app.database import AsyncSessionLocal
from app.jobs.generate_topic_analysis_job_enhanced import GenerateTopicAnalysisJob
from app.models import Topic, TopicSentimentBreakdown
from sqlalchemy import select, func

async def rerun():
    async with AsyncSessionLocal() as db:
        # Improved query: Topics with analysis but no breakdown (indicating they failed Step 5-8)
        # OR topics with no analysis at all
        from app.models import TopicAnalysis
        query = (
            select(Topic.id)
            .outerjoin(TopicSentimentBreakdown)
            .group_by(Topic.id)
            .having(func.count(TopicSentimentBreakdown.id) == 0)
        )
        
        result = await db.execute(query)
        topic_ids = result.scalars().all()
        logger.info(f"Re-analyzing {len(topic_ids)} topics")
        
        job = GenerateTopicAnalysisJob(db)
        for t_id in topic_ids:
            try:
                # Need a fresh session for each job to avoid state issues or handle them carefully
                async with AsyncSessionLocal() as job_db:
                    job = GenerateTopicAnalysisJob(job_db)
                    logger.info(f"  Analyzing topic {t_id}...")
                    await job.execute(t_id)
            except Exception as e:
                logger.error(f"  Failed topic {t_id}: {e}")

if __name__ == "__main__":
    asyncio.run(rerun())
