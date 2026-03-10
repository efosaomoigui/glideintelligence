
import asyncio
import os
import sys

# Add parent dir to path to find 'app'
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import AsyncSessionLocal
from app.models.settings import AIProvider
from sqlalchemy import select

async def main():
    print("Checking enabled AI providers...")
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(AIProvider).where(AIProvider.enabled==True).order_by(AIProvider.priority.desc()))
        providers = res.scalars().all()
        
        if not providers:
            print("No enabled providers found!")
        else:
            for p in providers:
                print(f"Provider: {p.name}, Model: {p.model}, Priority: {p.priority}")

if __name__ == "__main__":
    asyncio.run(main())
