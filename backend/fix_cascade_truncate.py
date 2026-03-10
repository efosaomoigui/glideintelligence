"""Quick fix: truncate topics and raw_articles with CASCADE to clear remaining FK-linked data."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def go():
    async with AsyncSessionLocal() as session:
        # TRUNCATE CASCADE handles any remaining FK children automatically
        await session.execute(text("TRUNCATE TABLE topics, raw_articles CASCADE"))
        await session.commit()
        # Verify
        r1 = await session.execute(text("SELECT COUNT(*) FROM topics"))
        r2 = await session.execute(text("SELECT COUNT(*) FROM raw_articles"))
        print(f"topics:       {r1.scalar()} rows remaining")
        print(f"raw_articles: {r2.scalar()} rows remaining")
        print("Done - database is now fully clean.")

asyncio.run(go())
