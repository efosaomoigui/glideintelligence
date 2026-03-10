
import asyncio
from app.database import AsyncSessionLocal
from app.models.topic import Topic, TopicAnalysis
from sqlalchemy import select

async def debug_query():
    async with AsyncSessionLocal() as db:
        print("\n--- Debugging Pipeline Selection Query ---")
        
        # 1. Check ALL topics
        res = await db.execute(select(Topic))
        all_topics = res.scalars().all()
        print(f"Total Topics: {len(all_topics)}")
        
        for t in all_topics:
            # Check for existing analysis
            res_a = await db.execute(select(TopicAnalysis).where(TopicAnalysis.topic_id == t.id))
            analysis = res_a.scalar_one_or_none()
            
            print(f"Topic {t.id}:")
            print(f"  - Category: {t.category} (Required: != None)")
            print(f"  - Status: {t.status} (Required: != 'analysis_failed')")
            print(f"  - Sentiment: {t.overall_sentiment} (Required: != 'error')")
            print(f"  - Has Analysis: {analysis is not None} (Required: False)")
            
            # Simulate query logic manually
            should_pick = (
                analysis is None and
                t.category is not None and
                t.status != 'analysis_failed' and
                t.overall_sentiment != 'error'
            )
            print(f"  -> Should be picked? {should_pick}")

if __name__ == "__main__":
    asyncio.run(debug_query())
