import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def wipe_content():
    async with AsyncSessionLocal() as session:
        print("Starting content wipe...")
        
        # Order matters for foreign keys
        tables_to_wipe = [
            # Topic related interactions/analysis
            "topic_videos",
            "topic_trends",
            "topic_analysis",
            "topic_sentiment_breakdown",
            "source_perspectives",
            "regional_impacts",
            "intelligence_cards",
            "ai_usage_logs",
            "ai_summaries",
            
            # Polls
            "poll_votes",
            "poll_options",
            "polls",
            
            # User interactions on content
            "comments",
            
            # Core Content
            "topic_articles",
            "topics",
            "article_embeddings",
            "article_entities",
            "raw_articles",
            
            # Jobs (to clear history)
            "jobs"
        ]
        
        try:
            for table in tables_to_wipe:
                print(f"Wiping table: {table}")
                # Use DELETE instead of TRUNCATE to avoid cascade issues with unlisted tables if any,
                # though TRUNCATE CASCADE is faster. DELETE is safer for targeted wipe.
                await session.execute(text(f"DELETE FROM {table}"))
                
            await session.commit()
            print("--- Wipe Complete ---")
            
            # Verify
            print("Verifying counts:")
            for table in tables_to_wipe:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count}")
                
            # Verify Sources preserved
            result = await session.execute(text("SELECT COUNT(*) FROM sources"))
            count = result.scalar()
            print(f"  sources: {count} (Should be > 0)")
            
        except Exception as e:
            print(f"Error during wipe: {e}")
            await session.rollback()

if __name__ == "__main__":
    import os
    import sys
    # Add backend dir to sys.path to allow imports
    sys.path.append(os.getcwd())
    
    asyncio.run(wipe_content())
