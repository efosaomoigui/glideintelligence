
import asyncio
from sqlalchemy import select, func, text
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis, TopicSentimentBreakdown, RegionalImpact, SourcePerspective, IntelligenceCard

async def check_data():
    async with AsyncSessionLocal() as db:
        print("Checking analysis data...")
        
        # 1. Get recent stable topics
        query = select(Topic).where(Topic.status == 'stable').order_by(Topic.updated_at.desc()).limit(5)
        result = await db.execute(query)
        topics = result.scalars().all()
        
        if not topics:
            print("No stable topics found.")
            return

        print(f"Found {len(topics)} recent stable topics.")
        
        for topic in topics:
            print(f"\nTopic ID: {topic.id} | Title: {topic.title[:50]}... | Category: {topic.category}")
            
            # Check TopicAnalysis
            q_ta = select(func.count(TopicAnalysis.id)).where(TopicAnalysis.topic_id == topic.id)
            c_ta = (await db.execute(q_ta)).scalar()
            print(f"  - TopicAnalysis rows: {c_ta}")
            
            # Check Sentiment Breakdown
            q_sb = select(func.count(TopicSentimentBreakdown.id)).where(TopicSentimentBreakdown.topic_id == topic.id)
            c_sb = (await db.execute(q_sb)).scalar()
            print(f"  - SentimentBreakdown rows: {c_sb}")
            
            # Check Regional Impact
            q_ri = select(func.count(RegionalImpact.id)).where(RegionalImpact.topic_id == topic.id)
            c_ri = (await db.execute(q_ri)).scalar()
            print(f"  - RegionalImpact rows: {c_ri}")

            # Check Source Perspectives
            q_sp = select(func.count(SourcePerspective.id)).where(SourcePerspective.topic_id == topic.id)
            c_sp = (await db.execute(q_sp)).scalar()
            print(f"  - SourcePerspective rows: {c_sp}")
            
            # Check Intelligence Card
            q_ic = select(func.count(IntelligenceCard.id)).where(IntelligenceCard.topic_id == topic.id)
            c_ic = (await db.execute(q_ic)).scalar()
            print(f"  - IntelligenceCard rows: {c_ic}")

            # Check if Category Config exists for this topic
            if topic.category:
                q_cc = text("SELECT count(*) FROM category_configs WHERE category = :cat")
                c_cc = (await db.execute(q_cc, {"cat": topic.category})).scalar()
                print(f"  - Category Config exists for '{topic.category}': {c_cc > 0}")
            else:
                print("  - Topic has no category!")

if __name__ == "__main__":
    asyncio.run(check_data())
