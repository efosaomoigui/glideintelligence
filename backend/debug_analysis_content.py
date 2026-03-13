
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis

async def inspect():
    async with AsyncSessionLocal() as db:
        print("=== Topic Analysis Status Summary ===")
        # Check analysis_status distribution
        from sqlalchemy import func
        res = await db.execute(select(Topic.analysis_status, func.count(Topic.id)).group_by(Topic.analysis_status))
        for row in res:
            print(f"Status: {row[0]} | Count: {row[1]}")

        print("\n=== Recent Topics and Analysis Content ===")
        # Get topics with complete analysis
        query = (
            select(Topic, TopicAnalysis)
            .join(TopicAnalysis, Topic.id == TopicAnalysis.topic_id)
            .order_by(Topic.updated_at.desc())
            .limit(5)
        )
        res = await db.execute(query)
        for topic, analysis in res:
            print(f"\nTopic ID: {topic.id} | Analysis Status: {topic.analysis_status}")
            print(f"Title: {topic.title}")
            print(f"Executive Summary Length: {len(analysis.executive_summary) if analysis.executive_summary else 0}")
            print(f"What you need to know: {len(analysis.what_you_need_to_know) if analysis.what_you_need_to_know else 'None'}")
            print(f"Key Takeaways: {len(analysis.key_takeaways) if analysis.key_takeaways else 'None'}")
            print(f"Drivers: {len(analysis.drivers_of_story) if analysis.drivers_of_story else 'None'}")
            print(f"Strategic: {len(analysis.strategic_implications) if analysis.strategic_implications else 'None'}")
            
            if analysis.executive_summary and len(analysis.executive_summary) < 50:
                 print(f"Executive Summary Snippet: '{analysis.executive_summary}'")

if __name__ == "__main__":
    asyncio.run(inspect())
