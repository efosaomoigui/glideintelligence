
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT category FROM category_configs"))
        cats = result.scalars().all()
        print(f"Existing Categories: {cats}")

if __name__ == "__main__":
    asyncio.run(check())
