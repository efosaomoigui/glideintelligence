import sys
import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy import select

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Load .env from backend dir
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal
from app.models.settings import AIProvider, AIProviderType

async def enable_local():
    async with AsyncSessionLocal() as db:
        print("Checking Local Provider...")
        
        result = await db.execute(select(AIProvider).where(AIProvider.name == "Local"))
        local = result.scalar_one_or_none()
        
        if not local:
            print("Creating Local Provider...")
            local = AIProvider(
                name="Local",
                # type=AIProviderType.OPEN_SOURCE, # Assuming OPEN_SOURCE is valid
                type=AIProviderType.OPEN_SOURCE,
                model="bart-large-cnn",
                enabled=True,
                priority=1 # Lower than Gemini (10)
            )
            db.add(local)
        else:
            print("Updating Local Provider...")
            local.enabled = True
            local.priority = 1
            local.type = AIProviderType.OPEN_SOURCE

        await db.commit()
        print("Local Provider Enabled and set to Priority 1.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enable_local())
