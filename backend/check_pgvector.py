import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

async def check_extension():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        row = result.first()
        if row:
            print("pgvector extension IS installed.")
        else:
            print("pgvector extension is NOT installed.")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_extension())
