import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("""
            SELECT type, status, error, started_at, completed_at
            FROM jobs
            ORDER BY started_at DESC
            LIMIT 15
        """))
        rows = r.fetchall()
        print(f"\nAll recent jobs (newest first):")
        print(f"{'Type':<22} {'Status':<12} {'Started':<26} {'Error'}")
        print("-" * 100)
        for row in rows:
            error_str = (str(row[2]) or "")[:60] if row[2] else ""
            started = str(row[3])[:19] if row[3] else "N/A"
            print(f"  {str(row[0]):<20} {str(row[1]):<12} {started:<26} {error_str}")

asyncio.run(check())
