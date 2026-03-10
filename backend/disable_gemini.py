import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.config import settings
from app.models.settings import AIProvider

async def disable_gemini():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Disabling Gemini...")
        query = update(AIProvider).where(AIProvider.name.ilike("%gemini%")).values(enabled=False)
        await session.execute(query)
        await session.commit()
        print("Gemini disabled.")
        
        # Verify
        result = await session.execute(select(AIProvider).where(AIProvider.enabled == True))
        providers = result.scalars().all()
        print("Active Providers:")
        for p in providers:
            print(f"- {p.name}")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(disable_gemini())
