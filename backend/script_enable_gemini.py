import sys
import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy import select, update

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Load .env from backend dir
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal
from app.models.settings import AIProvider, AIProviderType

async def enable_gemini():
    async with AsyncSessionLocal() as db:
        print("Checking AI Providers...")
        
        # Check if Gemini exists
        result = await db.execute(select(AIProvider).where(AIProvider.name == "Gemini"))
        gemini = result.scalar_one_or_none()
        
        if not gemini:
            print("Creating Gemini Provider...")
            gemini = AIProvider(
                name="Gemini",
                # api_url not needed/supported

                api_key=os.getenv("GEMINI_API_KEY", "placeholder"),
                model="gemini-2.0-flash",
                type=AIProviderType.PAID,
                enabled=True,
                priority=10
            )
            db.add(gemini)
        else:
            print("Updating Gemini Provider...")
            gemini.enabled = True
            gemini.priority = 10
            # Ensure api key is updated if env var is present
            if os.getenv("GEMINI_API_KEY"):
                gemini.api_key = os.getenv("GEMINI_API_KEY")

        # Disable or lower priority of others (optional, but good for testing dispatch)
        # await db.execute(update(AIProvider).where(AIProvider.name != "Gemini").values(priority=5))
        
        await db.commit()
        print("Gemini Enabled and set to Priority 10.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enable_gemini())
