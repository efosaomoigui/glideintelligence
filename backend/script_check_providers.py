import sys
import os
import asyncio
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(os.path.join(os.getcwd(), ".env"))

from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.settings import AIProvider

async def check_providers():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AIProvider))
        providers = result.scalars().all()
        print(f"Found {len(providers)} AI Providers.")
        for p in providers:
            print(f"- {p.name} ({p.model}) Enabled={p.enabled}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_providers())
