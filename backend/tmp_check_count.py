import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT COUNT(*) FROM raw_articles"))
        count = r.scalar()
        print(f"raw_articles count: {count}")

        r2 = await s.execute(text("SELECT status, COUNT(*) FROM jobs WHERE type='FETCH_ARTICLES' GROUP BY status"))
        for row in r2.fetchall():
            print(f"  FETCH job status: {row[0]} = {row[1]}")

        r3 = await s.execute(text("SELECT source_id, COUNT(*) as cnt FROM raw_articles GROUP BY source_id ORDER BY cnt DESC LIMIT 10"))
        rows = r3.fetchall()
        if rows:
            print("\nTop sources by article count:")
            for row in rows:
                print(f"  source_id={row[0]}: {row[1]} articles")

asyncio.run(check())
