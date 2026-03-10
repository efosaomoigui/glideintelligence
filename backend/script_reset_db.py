import asyncio
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Load .env from backend dir
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal

async def reset_db():
    print("Starting DB Reset (Preserving Sources)...")
    async with AsyncSessionLocal() as db:
        # Disable foreign key checks temporarily to allow truncation
        # Note: Postgres doesn't have SET FOREIGN_KEY_CHECKS, but we can TRUNCATE with CASCADE
        
        # Truncate all tables in one go with CASCADE
        print("Truncating tables...")
        # Correct table names based on models
        # topic_analysis, topic_sentiment_breakdown are singular in model definition
        truncate_sql = "TRUNCATE TABLE jobs, source_health, topic_articles, topic_analysis, topic_trends, topic_videos, topic_sentiment_breakdown, article_embeddings, article_entities, raw_articles, topics CASCADE;"
        await db.execute(text(truncate_sql))
        await db.commit()
        
        # Deactivate BBC in a separate transaction block/step
        print("Deactivating BBC Business...")
        await db.execute(text("UPDATE sources SET is_active = false WHERE name = 'BBC Business';"))
        await db.commit()
        
        print("Reset Complete.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_db())
