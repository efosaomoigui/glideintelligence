
import asyncio
from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models import Job

async def clear_stuck_jobs():
    print("Connecting to database to clear stuck jobs...")
    async with AsyncSessionLocal() as db:
        # Find all jobs that are 'RUNNING'
        query = select(Job).where(Job.status == 'RUNNING')
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        print(f"Found {len(jobs)} stuck jobs.")
        
        # We can't update individual objects here easily without re-fetching or attaching to session properly if we iterate.
        # But since we just want to bulk update them all, raw SQL is safest and fastest.
        
        if jobs:
             # Bulk update for efficiency and simplicity
             # Use text() for raw SQL
             await db.execute(
                 text("UPDATE jobs SET status = 'FAILED', updated_at = NOW(), error = 'System Cleanup: Reset stuck job' WHERE status = 'RUNNING'")
             )
             await db.commit()
             print(f"All {len(jobs)} stuck jobs have been marked as FAILED.")
        else:
            print("No stuck jobs found.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(clear_stuck_jobs())
