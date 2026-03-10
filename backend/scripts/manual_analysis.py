import asyncio
import os
import sys

# Add parent directory to sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from app.jobs.generate_topic_analysis_job_enhanced import GenerateTopicAnalysisJob

async def run_manual_analysis(topic_ids):
    async with AsyncSessionLocal() as db:
        job = GenerateTopicAnalysisJob(db)
        for t_id in topic_ids:
            print(f"Analyzing topic {t_id}...")
            try:
                await job.execute(t_id)
                print(f"Successfully analyzed topic {t_id}")
            except Exception as e:
                print(f"Error analyzing topic {t_id}: {e}")

if __name__ == "__main__":
    topics = [367, 339]
    asyncio.run(run_manual_analysis(topics))
