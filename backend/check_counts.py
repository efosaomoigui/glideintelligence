import asyncio
from sqlalchemy import text
from app.database import engine

async def check_data_counts():
    async with engine.connect() as conn:
        res_articles = await conn.execute(text("SELECT COUNT(*) FROM raw_articles"))
        count_articles = res_articles.scalar()
        
        res_topics = await conn.execute(text("SELECT COUNT(*) FROM topics"))
        count_topics = res_topics.scalar()
        
        print(f"Articles: {count_articles}, Topics: {count_topics}")

if __name__ == "__main__":
    asyncio.run(check_data_counts())
