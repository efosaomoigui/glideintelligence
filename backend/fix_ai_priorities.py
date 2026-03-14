
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.settings import AIProvider

async def fix_priorities():
    async with AsyncSessionLocal() as db:
        print("Updating AI Provider priorities...")
        # Make Claude highest priority
        await db.execute(
            update(AIProvider)
            .where(AIProvider.name.ilike('%claude%'))
            .values(priority=300, enabled=True)
        )
        
        # Make Gemini lower priority (fallback)
        await db.execute(
            update(AIProvider)
            .where(AIProvider.name.ilike('%gemini%'))
            .values(priority=200, enabled=True)
        )
        
        await db.commit()
        
        # Verify
        res = await db.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
        providers = res.scalars().all()
        print("\nUpdated Priorities:")
        for p in providers:
            print(f"- {p.name}: {p.priority} (Enabled: {p.enabled})")

if __name__ == "__main__":
    asyncio.run(fix_priorities())
