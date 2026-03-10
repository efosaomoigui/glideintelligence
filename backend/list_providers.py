import asyncio
from app.database import AsyncSessionLocal
from app.models.settings import AIProvider
from sqlalchemy import select

async def list_providers():
    async with AsyncSessionLocal() as db:
        query = select(AIProvider).where(AIProvider.enabled == True).order_by(AIProvider.priority.desc())
        result = await db.execute(query)
        providers = result.scalars().all()
        
        print(f"\n--- ENABLED AI PROVIDERS ---")
        if not providers:
            print("No enabled providers found.")
        for p in providers:
            print(f"ID: {p.id} | Name: {p.name} | Model: {p.model} | Priority: {p.priority}")

if __name__ == "__main__":
    asyncio.run(list_providers())
