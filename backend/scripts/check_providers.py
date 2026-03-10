
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.settings import AIProvider

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
        providers = res.scalars().all()
        for p in providers:
            print(f"{p.name} ({p.model}): Enabled={p.enabled}, Priority={p.priority}")
            
if __name__ == "__main__":
    asyncio.run(check())
