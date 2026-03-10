
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        print("Checking DB counts...")
        tables = ["raw_articles", "article_embeddings", "topics", "topic_articles", "topic_analysis", "intelligence_cards"]
        for t in tables:
            try:
                c = (await db.execute(text(f"SELECT COUNT(*) FROM {t}"))).scalar()
                print(f"{t}: {c}")
            except Exception as e:
                print(f"{t}: Error {e}")

if __name__ == "__main__":
    asyncio.run(check())
