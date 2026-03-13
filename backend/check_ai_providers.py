import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.settings import AIProvider

async def check_providers():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(AIProvider))
        providers = result.scalars().all()
        
        if not providers:
            print("No AI Providers found.")
        else:
            print(f"Found {len(providers)} AI Providers:")
            for p in providers:
                has_key = "Yes" if p.api_key else "No"
                print(f"- {p.name} ({p.model}) [Enabled: {p.enabled}] Priority: {p.priority} | Key: {has_key}")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_providers())
