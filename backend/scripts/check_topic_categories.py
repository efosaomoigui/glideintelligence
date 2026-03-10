
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models import Topic

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Topic.category, func.count(Topic.id)).group_by(Topic.category))
        rows = res.all()
        for r in rows:
            print(f"{r[0]}: {r[1]}")
            
if __name__ == "__main__":
    asyncio.run(check())
