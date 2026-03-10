import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Load .env from backend dir
load_dotenv(os.path.join(BASE_DIR, ".env"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.source import Source

async def list_sources():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Source))
        sources = result.scalars().all()
        print(f"Found {len(sources)} sources:")
        for s in sources:
            print(f"- [{s.id}] {s.name} ({s.url}) Active={s.is_active}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(list_sources())
