
import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models import Topic, RawArticle
from sqlalchemy import select

async def check_tech_category():
    async with AsyncSessionLocal() as db:
        # Check Topics
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
            
        result = await db.execute(select(Topic).where(Topic.category == 'tech'))
        topics = result.scalars().all()
        print(f"Found {len(topics)} topics with category 'tech':")
        for t in topics:
            try:
                print(f"  - ID: {t.id}, Title: {t.title}")
            except UnicodeEncodeError:
                print(f"  - ID: {t.id}, Title: {t.title.encode('ascii', 'replace').decode()}")

        # Check Articles
        result = await db.execute(select(RawArticle).where(RawArticle.category == 'tech'))
        articles = result.scalars().all()
        print(f"\nFound {len(articles)} articles with category 'tech':")
        for a in articles:
            try:
                print(f"  - ID: {a.id}, Title: {a.title}")
            except UnicodeEncodeError:
                 print(f"  - ID: {a.id}, Title: {a.title.encode('ascii', 'replace').decode()}")

        # Check for 'Technology' to compare
        result = await db.execute(select(Topic).where(Topic.category == 'technology'))
        tech_topics = result.scalars().all()
        print(f"\nFound {len(tech_topics)} topics with category 'technology'")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_tech_category())
