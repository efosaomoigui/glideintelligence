import os
import sys
import asyncio
from sqlalchemy import select, func

# Add backend to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models.topic import TopicAnalysis

async def count_analysis():
    async with AsyncSessionLocal() as db:
        stmt = select(func.count(TopicAnalysis.id))
        result = await db.execute(stmt)
        count = result.scalar()
        print(f"Total TopicAnalysis records: {count}")
        
        # Also check for topic 801 specifically
        stmt2 = select(TopicAnalysis).where(TopicAnalysis.topic_id == 801)
        result2 = await db.execute(stmt2)
        analysis = result2.scalar_one_or_none()
        if analysis:
            print("Analysis for topic 801 found.")
        else:
            print("Analysis for topic 801 NOT found.")

if __name__ == "__main__":
    asyncio.run(count_analysis())
