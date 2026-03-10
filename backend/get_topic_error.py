
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Topic

async def get_error():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Topic.metadata_).where(Topic.id == 561))
        meta = result.scalar_one_or_none()
        print(f"Metadata: {meta}")

if __name__ == "__main__":
    asyncio.run(get_error())
