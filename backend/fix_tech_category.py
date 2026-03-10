
import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models import Topic, RawArticle
from sqlalchemy import select, update

async def fix_tech_category():
    async with AsyncSessionLocal() as db:
        print("Fixing 'tech' category in Topics...")
        # Fix Topics
        stmt = update(Topic).where(Topic.category == 'tech').values(category='technology')
        result = await db.execute(stmt)
        print(f"  Updated {result.rowcount} topics.")

        print("\nFixing 'tech' category in Articles...")
        # Fix Articles
        stmt = update(RawArticle).where(RawArticle.category == 'tech').values(category='technology')
        result = await db.execute(stmt)
        print(f"  Updated {result.rowcount} articles.")

        await db.commit()
        print("\n[SUCCESS] access fixed.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_tech_category())
