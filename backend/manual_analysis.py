import asyncio
import os
import sys
from app.database import AsyncSessionLocal
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
from app.models.topic import Topic

async def run_manual_analysis(topic_id: int):
    print(f"Running manual analysis for Topic ID: {topic_id}...")
    async with AsyncSessionLocal() as db:
        # Check if topic exists
        topic = await db.get(Topic, topic_id)
        if not topic:
            print(f"Topic {topic_id} not found!")
            return
            
        print(f"Topic Title: {topic.title}")
        
        # Initialize and run job
        job = GenerateTopicAnalysisJob(db)
        try:
            await job.execute(topic_id)
            print(f"SUCCESS: Analysis generated for topic {topic_id}")
            
            # Refresh and check description
            await db.refresh(topic)
            print(f"Updated Description: {topic.description[:100]}...")
            
        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    if len(sys.argv) < 2:
        print("Usage: python manual_analysis.py <topic_id>")
        sys.exit(1)
        
    asyncio.run(run_manual_analysis(int(sys.argv[1])))
