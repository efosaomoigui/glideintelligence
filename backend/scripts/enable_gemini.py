import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def enable_gemini():
    print("Enabling Gemini Provider...")
    async for session in get_db():
        try:
            stmt = text("UPDATE ai_providers SET enabled = true WHERE name = 'Gemini'")
            await session.execute(stmt)
            await session.commit()
            print("Gemini enabled successfully.")
        except Exception as e:
            print(f"Error enabling Gemini: {e}")
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enable_gemini())
