import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def check_providers():
    print("Checking AI Providers...")
    async for session in get_db():
        try:
            stmt = text("SELECT id, name, type, enabled, priority, model FROM ai_providers ORDER BY priority DESC")
            result = (await session.execute(stmt)).all()
            
            if not result:
                print("No AI providers found.")
            else:
                print(f"Found {len(result)} AI providers:")
                for row in result:
                    print(f"ID: {row.id}, Name: {row.name}, Type: {row.type}, Enabled: {row.enabled}, Priority: {row.priority}, Model: {row.model}")
                    
        except Exception as e:
            print(f"Error checking providers: {e}")
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_providers())
