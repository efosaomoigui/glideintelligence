import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.settings import AIProvider, AIProviderType

async def seed_providers():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        providers = [
            {
                "name": "Gemini",
                "type": AIProviderType.PAID,
                "api_key": os.getenv("GEMINI_API_KEY", "pending"),
                "model": "gemini-pro",
                "enabled": True,
                "priority": 10
            },
            {
                "name": "Local (BART)",
                "type": AIProviderType.OPEN_SOURCE,
                "api_key": None,
                "model": "facebook/bart-large-cnn",
                "enabled": True,
                "priority": 5
            }
        ]
        
        for p_data in providers:
            stmt = select(AIProvider).where(AIProvider.name == p_data["name"])
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                print(f"Adding Provider: {p_data['name']}")
                session.add(AIProvider(**p_data))
            else:
                print(f"Provider {p_data['name']} already exists.")
        
        await session.commit()
        print("Seeding AI Providers Complete!")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_providers())
