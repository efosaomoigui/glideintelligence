import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def get_tables():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        for row in res.fetchall():
            print(row[0])

if __name__ == "__main__":
    asyncio.run(get_tables())
