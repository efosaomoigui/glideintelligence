"""
run_analysis_all.py
Batch-process analysis for ALL topics that have no completed analysis.
Runs GenerateTopicAnalysisJob in batches until all topics are done.
"""

import asyncio
import time
from sqlalchemy import select, or_
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
from app.services.ai.content_generator import RateLimiter, CostTracker
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

MAX_PARALLEL = int(os.getenv('MAX_PARALLEL_TOPICS', '2'))       # Keep low to respect Gemini rate limit
DAILY_BUDGET = float(os.getenv('DAILY_BUDGET_USD', '10.0'))     # Raise budget if needed
BATCH_LIMIT  = int(os.getenv('BATCH_LIMIT', '200'))             # How many topics to attempt total

rate_limiter = RateLimiter()
cost_tracker = CostTracker()
semaphore    = asyncio.Semaphore(MAX_PARALLEL)

succeeded = []
failed    = []

async def process_one(topic_id: int, title: str, category: str):
    async with semaphore:
        try:
            async with AsyncSessionLocal() as db:
                job = GenerateTopicAnalysisJob(db, rate_limiter, cost_tracker)
                await job.execute(topic_id)
            logger.info(f"✅ [{category}] {title[:55]}")
            succeeded.append(topic_id)
        except Exception as e:
            logger.error(f"❌ [{category}] {title[:55]} — {str(e)[:120]}")
            failed.append(topic_id)

async def main():
    start = time.time()

    # Fetch all topics that still need analysis
    async with AsyncSessionLocal() as db:
        # Topics that have no entry in topic_analysis OR status != stable
        pending_query = (
            select(Topic)
            .outerjoin(TopicAnalysis, TopicAnalysis.topic_id == Topic.id)
            .where(
                or_(
                    TopicAnalysis.id == None,
                    Topic.status != 'stable'
                )
            )
            .limit(BATCH_LIMIT)
        )
        result = await db.execute(pending_query)
        pending = result.unique().scalars().all()

    logger.info(f"Found {len(pending)} topics needing analysis (budget=${DAILY_BUDGET}, parallel={MAX_PARALLEL})")

    # Process in chunks so we can report progress
    CHUNK = 20
    for i in range(0, len(pending), CHUNK):
        chunk = pending[i:i+CHUNK]
        logger.info(f"\n--- Chunk {i//CHUNK + 1}: topics {i+1}–{min(i+CHUNK, len(pending))} ---")

        if not cost_tracker.can_process(DAILY_BUDGET):
            logger.warning(f"Daily budget ${DAILY_BUDGET:.2f} reached — stopping.")
            break

        tasks = [process_one(t.id, t.title, t.category or 'unknown') for t in chunk]
        await asyncio.gather(*tasks)

        logger.info(f"Progress: {len(succeeded)} ok, {len(failed)} failed so far")

    elapsed = time.time() - start
    print("\n" + "="*70)
    print(f"ANALYSIS RUN COMPLETE")
    print(f"  Topics processed : {len(succeeded) + len(failed)}")
    print(f"  Succeeded        : {len(succeeded)}")
    print(f"  Failed           : {len(failed)}")
    print(f"  Time elapsed     : {elapsed:.1f}s")
    print(f"  Tokens used      : {cost_tracker.tokens_used:,}")
    print(f"  Cost today       : ${cost_tracker.get_today_cost():.4f}")
    if failed:
        print(f"\n  Failed topic IDs: {failed}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
