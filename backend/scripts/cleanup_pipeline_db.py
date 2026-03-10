import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import text
from app.database import AsyncSessionLocal

# Equivalent mapped tables for Phase 2 Pipeline Cleanup
# pipeline_jobs -> jobs
# pipeline_logs -> ai_usage_logs
# ai_processing_queue -> collection_jobs
# normalized_articles_temp -> raw_articles

TABLES_TO_CLEAN = [
    "jobs",
    "ai_usage_logs",
    "collection_jobs",
    "raw_articles"
]

async def cleanup_pipeline():
    async with AsyncSessionLocal() as session:
        print("--- Starting AI Pipeline DB Cleanup ---")
        
        # Check counts before
        print("\nCounts before cleanup:")
        for table in TABLES_TO_CLEAN:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count}")
            except Exception as e:
                print(f"  {table}: Error checking count - {e}")

        # Execute Truncate
        print("\nCleaning AI pipeline tables...\n")
        all_tables_str = ", ".join(TABLES_TO_CLEAN)
        try:
            await session.execute(text(f"TRUNCATE TABLE {all_tables_str} RESTART IDENTITY CASCADE"))
            await session.commit()
            print("Successfully truncated all pipeline tables.")
        except Exception as e:
            await session.rollback()
            print(f"Error during truncate using CASCADE: {e}")
            print("\nAttempting DELETE from each table individually...")
            for table in TABLES_TO_CLEAN:
                try:
                    await session.execute(text(f"DELETE FROM {table}"))
                    print(f"  Cleared {table}")
                except Exception as del_e:
                    print(f"  Failed to clear {table}: {del_e}")
            await session.commit()

        # Check counts after
        print("\nCounts after cleanup:")
        for table in TABLES_TO_CLEAN:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count}")
            except Exception as e:
                print(f"  {table}: Error checking count - {e}")
        
        print("\n--- Pipeline Cleanup Complete ---")

if __name__ == "__main__":
    asyncio.run(cleanup_pipeline())
