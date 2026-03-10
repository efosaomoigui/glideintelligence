"""
reset_pipeline.py
Wipes ONLY pipeline-generated article and topic data, then resets sequences.

PROTECTED (never wiped):
  - sources           (manually seeded news sources)
  - ai_providers      (configuration)
  - category_configs  (configuration)
  - impact_categories (seeded lookup data)
  - feature_flags     (configuration)
"""

import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

# Only pipeline-generated tables — NOT config/seed tables
WIPE_SQL = """
TRUNCATE TABLE
    intelligence_cards,
    impact_details,
    regional_impacts,
    topic_sentiment_breakdown,
    source_perspectives,
    topic_analysis,
    topic_trends,
    article_entities,
    article_embeddings,
    topic_articles,
    topics,
    raw_articles
RESTART IDENTITY CASCADE;
"""

async def wipe_data():
    async with AsyncSessionLocal() as db:
        print("Wiping pipeline-generated data only...")
        print("(sources, ai_providers, category_configs, impact_categories are preserved)")
        await db.execute(text(WIPE_SQL))
        await db.commit()
        print("[OK] Pipeline data wiped successfully.\n")

if __name__ == "__main__":
    asyncio.run(wipe_data())
    print("Database reset complete.")
    print("Now run the pipeline: python run_pipeline.py")

