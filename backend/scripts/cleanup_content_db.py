import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import text
from app.database import AsyncSessionLocal

TABLES_TO_CLEAN = [
    # Core Analysis & Topics
    "topic_tags", "topic_videos", "topic_trends", "summary_updates", 
    "ai_summaries", "topic_sentiment_breakdown", "topic_analysis", 
    "topic_articles", "topics",
    
    # Articles & Data Sources
    "youtube_videos", "article_embeddings", "collection_jobs", "raw_articles",
    "article_entities",
    
    # Intelligence Portal
    "intelligence_cards", "source_perspectives",
    
    # Perspectives & Sentiments
    "perspective_quotes", "topic_perspectives", "sentiment_analysis",
    
    # Regional Impacts
    "impact_metrics", "impact_details", "regional_impacts",
    
    # Community & Interactions
    "community_insights", "poll_votes", "poll_options", "polls", 
    "comment_votes", "comments",
    
    # Execution & Tracking
    "jobs", "ai_usage_logs", "audit_logs", "analytics_events"
]

async def cleanup_content():
    async with AsyncSessionLocal() as session:
        print("--- Starting Full Content Database Wipe ---")
        print("NOTE: Configuration tables (users, sources, category_configs, ai_providers) are PRESERVED.")
        
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
        print("\nCleaning tables...")
        all_tables_str = ", ".join(TABLES_TO_CLEAN)
        try:
            await session.execute(text(f"TRUNCATE TABLE {all_tables_str} RESTART IDENTITY CASCADE"))
            await session.commit()
            print("Successfully truncated all generated content tables.")
        except Exception as e:
            await session.rollback()
            print(f"Error during truncate: {e}")
            print("Attempting delete from each table individually...")
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
        
        print("\n--- Content Cleanup Complete ---")

if __name__ == "__main__":
    asyncio.run(cleanup_content())
