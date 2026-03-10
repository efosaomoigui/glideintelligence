import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name LIKE '%topic%' ORDER BY table_name"
        ))
        print("Tables with 'topic' in name:")
        for row in r.fetchall():
            print(f"  {row[0]}")
        
        r2 = await s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name LIKE '%analys%' ORDER BY table_name"
        ))
        print("\nTables with 'analys' in name:")
        for row in r2.fetchall():
            print(f"  {row[0]}")

if __name__ == "__main__":
    asyncio.run(check())
