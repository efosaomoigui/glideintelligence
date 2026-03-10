import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def update_gemini_model():
    print("Updating Gemini Model to gemini-1.5-flash...")
    async for session in get_db():
        try:
            stmt = text("UPDATE ai_providers SET model = 'gemini-2.0-flash' WHERE name = 'Gemini'")
            await session.execute(stmt)
            await session.commit()
            print("Gemini model updated successfully.")
        except Exception as e:
            print(f"Error updating Gemini model: {e}")
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(update_gemini_model())
