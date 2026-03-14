import asyncio
from sqlalchemy import text
from app.database import engine

async def check_db_schema():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'raw_articles' AND column_name = 'published_at';
        """))
        row = result.fetchone()
        if row:
            print(f"Column: {row[0]}, Type: {row[1]}")
        else:
            print("Column published_at not found in raw_articles")

if __name__ == "__main__":
    asyncio.run(check_db_schema())
