import asyncio
import sys
import os
from pathlib import Path

# Add current dir to sys.path for app imports
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models.intelligence import CategoryConfig
from app.constants import VALID_CATEGORIES
from sqlalchemy import delete

async def cleanup():
    async with AsyncSessionLocal() as db:
        print(f"Valid categories: {VALID_CATEGORIES}")
        # Delete any category not in the VALID_CATEGORIES set
        stmt = delete(CategoryConfig).where(CategoryConfig.category.notin_(VALID_CATEGORIES))
        result = await db.execute(stmt)
        await db.commit()
        print(f"Deleted {result.rowcount} orphaned categories.")

if __name__ == "__main__":
    asyncio.run(cleanup())
