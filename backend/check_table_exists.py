import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.getcwd())
from app.config import settings

async def check_table():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT to_regclass('public.jobs')"))
        exists = result.scalar()
        print(f"Table 'jobs' exists: {exists is not None}")
        
        result = await conn.execute(text("SELECT to_regclass('public.collection_jobs')"))
        exists = result.scalar()
        print(f"Table 'collection_jobs' exists: {exists is not None}")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_table())
