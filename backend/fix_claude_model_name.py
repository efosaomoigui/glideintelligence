import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.settings import AIProvider

async def update_claude_model():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Update Claude model name
        stmt = (
            update(AIProvider)
            .where(AIProvider.name.ilike('%claude%'))
            .values(model="claude-opus-4-6")
        )
        await session.execute(stmt)
        await session.commit()
        print("Updated Claude model to 'claude-opus-4-6'.")
        
        # Verify
        result = await session.execute(select(AIProvider).where(AIProvider.name.ilike('%claude%')))
        provider = result.scalar_one_or_none()
        if provider:
            print(f"Verified: {provider.name} model is now {provider.model}")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(update_claude_model())
