import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import RawArticle

async def check():
    async with AsyncSessionLocal() as db:
        print("Checking HTML residue...")
        query = select(RawArticle).where(RawArticle.content.like('%<p>%'))
        res = await db.execute(query)
        html_articles = res.scalars().all()
        print(f"Articles with <p> tags: {len(html_articles)}")
        
        print("\nChecking categories...")
        query = select(RawArticle.category).distinct()
        res = await db.execute(query)
        categories = res.scalars().all()
        print(f"Unique categories: {categories}")

if __name__ == "__main__":
    asyncio.run(check())
