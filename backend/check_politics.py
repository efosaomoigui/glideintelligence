import asyncio
from app.database import async_session_maker
from app.models.topic import Topic
from app.models.article import RawArticle
from sqlalchemy import select, func

async def main():
    async with async_session_maker() as db:
        topics = (await db.execute(select(func.count(Topic.id)).where(func.lower(Topic.category) == 'politics'))).scalar()
        articles = (await db.execute(select(func.count(RawArticle.id)).where(func.lower(RawArticle.category) == 'politics'))).scalar()
        print(f"Politics - Topics: {topics}, Articles: {articles}")

if __name__ == "__main__":
    asyncio.run(main())
