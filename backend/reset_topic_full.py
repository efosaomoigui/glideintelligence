
import asyncio
from sqlalchemy import select, delete
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis, TopicSentimentBreakdown, RegionalImpact, SourcePerspective, IntelligenceCard

TOPIC_ID = 561

async def reset_topic():
    async with AsyncSessionLocal() as db:
        print(f"Resetting Topic {TOPIC_ID}...")
        
        # 1. Clear Analysis
        await db.execute(delete(TopicAnalysis).where(TopicAnalysis.topic_id == TOPIC_ID))
        await db.execute(delete(TopicSentimentBreakdown).where(TopicSentimentBreakdown.topic_id == TOPIC_ID))
        await db.execute(delete(RegionalImpact).where(RegionalImpact.topic_id == TOPIC_ID))
        await db.execute(delete(SourcePerspective).where(SourcePerspective.topic_id == TOPIC_ID))
        await db.execute(delete(IntelligenceCard).where(IntelligenceCard.topic_id == TOPIC_ID))
        
        # 2. Reset Status
        t_res = await db.execute(select(Topic).where(Topic.id == TOPIC_ID))
        topic = t_res.scalar_one_or_none()
        if topic:
            topic.status = 'developing'
            topic.overall_sentiment = None
            print(f"Topic {TOPIC_ID} status reset to 'developing'.")
        else:
            print(f"Topic {TOPIC_ID} not found.")
            
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(reset_topic())
