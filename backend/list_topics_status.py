import asyncio
import os
import sys
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis

async def list_topics():
    async with AsyncSessionLocal() as db:
        query = select(Topic).order_by(Topic.created_at.desc())
        result = await db.execute(query)
        topics = result.scalars().all()
        
        print(f"{'ID':<5} | {'TITLE':<40} | {'STATUS':<15} | {'HAS ANALYSIS'}")
        print("-" * 80)
        for t in topics:
            analysis_query = select(TopicAnalysis).where(TopicAnalysis.topic_id == t.id)
            analysis_res = await db.execute(analysis_query)
            has_analysis = "YES" if analysis_res.scalar_one_or_none() else "NO"
            
            title = (t.title[:37] + "...") if len(t.title) > 37 else t.title
            print(f"{t.id:<5} | {title:<40} | {t.status:<15} | {has_analysis}")

if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    asyncio.run(list_topics())
