
import asyncio
from app.database import AsyncSessionLocal
from app.models.settings import AIProvider
from sqlalchemy import select

async def prioritize_ollama():
    async with AsyncSessionLocal() as db:
        print("Checking provider configuration...")
        
        # Disable all cloud providers or lower their priority
        result = await db.execute(select(AIProvider))
        providers = result.scalars().all()
        
        for p in providers:
            if "ollama" in p.name.lower():
                p.enabled = True
                p.priority = 100  # Highest priority
                print(f"  [UPDATED] {p.name} -> Enabled, Priority 100")
            elif "gemini" in p.name.lower():
                p.enabled = False 
                p.priority = 10   # Lower, but disabled
                print(f"  [UPDATED] {p.name} -> Disabled")
            else:
                p.priority = 1
                
        await db.commit()
        print("Configuration updated: Ollama is now primary.")

if __name__ == "__main__":
    asyncio.run(prioritize_ollama())
