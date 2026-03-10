import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def switch_to_ollama():
    print("Switching AI Provider to Ollama...")
    async for session in get_db():
        try:
            # Disable Gemini
            await session.execute(text("UPDATE ai_providers SET enabled = false WHERE name = 'Gemini'"))
            
            # Enable Ollama and set high priority
            # Check if Ollama exists
            res = await session.execute(text("SELECT id FROM ai_providers WHERE name = 'Ollama'"))
            if res.first():
                await session.execute(text("UPDATE ai_providers SET enabled = true, priority = 100 WHERE name = 'Ollama'"))
                print("Ollama enabled with priority 100.")
            else:
                print("Ollama provider not found in DB!")
            
            await session.commit()
            print("AI Providers updated.")
        except Exception as e:
            print(f"Error switching provider: {e}")
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(switch_to_ollama())
