
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import Topic

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Topic).where(Topic.status == 'analysis_failed').limit(10))
        topics = res.scalars().all()
        
        if not topics:
            print("No topics found with status 'analysis_failed'")
            # Check topics with 'stable' but no breakdown
            from app.models import TopicAnalysis, TopicSentimentBreakdown
            res = await db.execute(
                select(Topic)
                .join(TopicAnalysis)
                .outerjoin(TopicSentimentBreakdown)
                .where(TopicSentimentBreakdown.id == None)
                .limit(5)
            )
            topics = res.scalars().all()
            print(f"Found {len(topics)} topics with analysis but no breakdown")
        
        for t in topics:
            print(f"Topic ID: {t.id}, Status: {t.status}, Metadata: {t.metadata_}")

if __name__ == "__main__":
    asyncio.run(check())
