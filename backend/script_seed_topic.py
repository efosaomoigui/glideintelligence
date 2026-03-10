import asyncio
import sys
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis, TopicSentimentBreakdown
from sqlalchemy import select, delete

async def seed_topic():
    print("Seeding test topic...")
    async with AsyncSessionLocal() as db:
        # Check if exists and delete
        stmt = select(Topic).where(Topic.title == "Fuel Subsidy Removal")
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            print("Topic exists, deleting clean...")
            await db.delete(existing)
            await db.commit()

        # Create Topic
        topic = Topic(
            title="Fuel Subsidy Removal",
            description="Analysis of the recent removal of fuel subsidies in Nigeria.",
            is_trending=True,
            confidence_score=0.92,
            source_count=15,
            coverage_level="high"
        )
        db.add(topic)
        await db.flush() # Get ID

        # Create Analysis
        analysis = TopicAnalysis(
            topic_id=topic.id,
            summary="The removal of fuel subsidies has led to a 200% increase in petrol prices, triggering nationwide protests. The government argues this is necessary for long-term economic stability, while labor unions demand immediate palliatives.",
            regional_framing={
                "impact_score": 9,
                "economic_impact": "High inflation and transportation costs affecting all sectors.",
                "political_impact": "Loss of political capital for the ruling party; increased opposition activity.",
                "social_impact": "Widespread dissatisfaction and calls for industrial action."
            },
            facts=["Price hike to N600/liter", "NLC threatens strike", "Government saves N400bn monthly"]
        )
        db.add(analysis)

        # Create Sentiment
        sentiment = TopicSentimentBreakdown(
            topic_id=topic.id,
            positive=0.1,
            neutral=0.2,
            negative=0.7
        )
        db.add(sentiment)

        await db.commit()
        print(f"Topic seeded: {topic.title} (ID: {topic.id})")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_topic())
