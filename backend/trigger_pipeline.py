import asyncio
import sys
import os

backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.workers.tasks import clustering_job

async def trigger():
    print("Triggering clustering_job...")
    job_id = clustering_job.delay()
    print(f"Triggered clustering_job: {job_id}")

if __name__ == "__main__":
    asyncio.run(trigger())
