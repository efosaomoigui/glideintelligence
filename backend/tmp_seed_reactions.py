import asyncio
from app.database import AsyncSessionLocal
from app.models.topic import Topic, TopicSocialReaction
from sqlalchemy import select

async def seed():
    async with AsyncSessionLocal() as db:
        topic = (await db.execute(select(Topic).limit(1))).scalar_one_or_none()
        if topic:
            r1 = TopicSocialReaction(
                topic_id=topic.id, 
                platform='x', 
                author='TechTrend', 
                content_excerpt='Google AI search in Yoruba is a game changer for local education and accessibility in Nigeria! #GoogleAI #Yoruba', 
                url='https://x.com/techtrend/status/1', 
                engagement_score='1.2k Likes'
            )
            r2 = TopicSocialReaction(
                topic_id=topic.id, 
                platform='youtube', 
                author='LagosVibe', 
                content_excerpt='Deep dive into the new Google AI features for West Africa. How this impacts Nigerian businesses.', 
                url='https://youtube.com/watch?v=123', 
                engagement_score='50k Views'
            )
            db.add_all([r1, r2])
            await db.commit()
            print(f"Seeded reactions for topic {topic.id}")
        else:
            print("No topics found")

if __name__ == "__main__":
    asyncio.run(seed())
