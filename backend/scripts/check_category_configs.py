
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text('SELECT category FROM category_configs'))
        rows = res.all()
        if not rows:
            print("No category configs found!")
        for r in rows:
            print(f"Category: {r[0]}")
            
if __name__ == "__main__":
    asyncio.run(check())
