
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import text, select
from app.models import Topic, TopicAnalysis
from app.models.intelligence import CategoryConfig

async def check():
    async with AsyncSessionLocal() as db:
        # Check topic with analysis
        res = await db.execute(select(Topic).join(TopicAnalysis).limit(5))
        topics = res.scalars().all()
        
        for t in topics:
            print(f"Topic ID: {t.id}, Category: {t.category}")
            # Check config lookup
            cat = t.category.lower() if t.category else None
            config_res = await db.execute(select(CategoryConfig).where(CategoryConfig.category == cat))
            config = config_res.scalar_one_or_none()
            print(f"  Config Found: {config is not None}")
            
            # Check for breakdown
            from app.models import TopicSentimentBreakdown
            s_res = await db.execute(select(TopicSentimentBreakdown).where(TopicSentimentBreakdown.topic_id == t.id))
            sentiments = s_res.scalars().all()
            print(f"  Sentiments Count: {len(sentiments)}")

if __name__ == "__main__":
    asyncio.run(check())
