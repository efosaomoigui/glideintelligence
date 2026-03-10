
import asyncio
import sys
import os
from sqlalchemy import func

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis
from sqlalchemy import select

async def check_status():
    async with AsyncSessionLocal() as db:
        # Count by status
        stmt = select(Topic.status, func.count(Topic.id)).group_by(Topic.status)
        results = await db.execute(stmt)
        print("Topic Status Distribution:")
        for status, count in results.all():
            print(f"  {status}: {count}")
            
        # Count with analysis
        stmt = select(func.count(Topic.id)).join(TopicAnalysis)
        analyzed_count = (await db.execute(stmt)).scalar()
        
        total_topics = (await db.execute(select(func.count(Topic.id)))).scalar()
        
        print(f"\nTotal Topics: {total_topics}")
        print(f"Topics with Analysis: {analyzed_count}")
        print(f"Topics needing Analysis: {total_topics - analyzed_count}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_status())
