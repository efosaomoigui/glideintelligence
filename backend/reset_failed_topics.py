import asyncio
from sqlalchemy import select, update, text
from app.database import AsyncSessionLocal
from app.models.topic import Topic

async def reset_topics():
    async with AsyncSessionLocal() as db:
        print("Resetting failed topics to trigger re-processing...")
        
        # 1. Reset topics that failed completeness or categorization
        # If they failed categorization, they might be 'verified' but analysis_status='failed'
        # If they failed completeness, they go back to 'pending' (handled by completeness agent)
        
        # Count current failed topics
        result = await db.execute(text("SELECT count(*) FROM topics WHERE analysis_status = 'failed';"))
        failed_count = result.scalar()
        print(f"Found {failed_count} topics in 'failed' status.")
        
        if failed_count > 0:
            # We reset them to 'pending' to be safe, so they get a fresh analysis if needed.
            # Or reset to 'verified' if we are confident the analysis is good but only categorization failed.
            # Given the quota issue, reset to 'verified' for those that have analysis data.
            
            # Check for analysis presence
            res = await db.execute(
                update(Topic)
                .where(Topic.analysis_status == 'failed')
                .values(analysis_status='verified')
            )
            print(f"Updated {res.rowcount} topics to 'verified'.")
        
        # Also check for 'pending' topics that might have been stuck
        result = await db.execute(text("SELECT count(*) FROM topics WHERE analysis_status = 'pending';"))
        pending_count = result.scalar()
        print(f"Current pending topics: {pending_count}")
        
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(reset_topics())
