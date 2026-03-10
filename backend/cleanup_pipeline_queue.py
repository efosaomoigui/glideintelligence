import asyncio
import os
import sys
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.models import Job

async def cleanup_queue():
    print("Clearing stale RUNNING jobs in DB...")
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Job)
            .where(Job.status == "RUNNING")
            .values(status="FAILED", error="Stale job cleared during maintenance")
        )
        await db.commit()
    print("Done clearing DB.")

    print("Purging Celery queue...")
    # Using python -m celery purge directly via subprocess
    import subprocess
    try:
        result = subprocess.run(
            ["python", "-m", "celery", "-A", "app.workers.celery_app", "purge", "-f"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Error purging: {result.stderr}")
    except Exception as e:
        print(f"Failed to run purge: {e}")

if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    asyncio.run(cleanup_queue())
