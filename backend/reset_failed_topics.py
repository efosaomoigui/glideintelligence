
import asyncio
import sys
import os
from sqlalchemy import update

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models import Topic
from sqlalchemy import select

async def reset_topics():
    async with AsyncSessionLocal() as db:
        # Find 10 failed topics
        stmt = select(Topic).where(Topic.status == 'analysis_failed').limit(10)
        result = await db.execute(stmt)
        topics = result.scalars().all()
        
        print(f"Found {len(topics)} failed topics to reset.")
        
        if not topics:
            return

        ids = [t.id for t in topics]
        
        # Reset them
        update_stmt = update(Topic).where(Topic.id.in_(ids)).values(
            status='developing',  # or whatever initial status is appropriate
            overall_sentiment=None,
            metadata_=None # content_generator logic might check metadata for errors
        )
        await db.execute(update_stmt)
        await db.commit()
        
        print(f"Reset topics: {ids}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_topics())
