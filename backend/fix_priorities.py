
import asyncio
import os
import sys

# Add parent dir to path to find 'app'
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import AsyncSessionLocal
from app.models.settings import AIProvider
from sqlalchemy import select, update

async def main():
    print("Fixing AI provider priorities...")
    async with AsyncSessionLocal() as session:
        # Get providers
        res = await session.execute(select(AIProvider))
        providers = res.scalars().all()
        
        for p in providers:
            original_p = p.priority
            if p.name.lower() == "gemini":
                p.priority = 100
                print(f"Updated Gemini priority: {original_p} -> 100")
            elif p.name.lower() == "ollama":
                p.priority = 10
                print(f"Updated Ollama priority: {original_p} -> 10")
            else:
                p.priority = 5
                print(f"Updated {p.name} priority: {original_p} -> 5")
            
            session.add(p)
        
        await session.commit()
        print("Priorities updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
