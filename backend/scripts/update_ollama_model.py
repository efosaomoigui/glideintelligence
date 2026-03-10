
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import update
from app.models.settings import AIProvider

async def update_model():
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(AIProvider)
            .where(AIProvider.name == 'Ollama')
            .values(model='llama3:latest')
        )
        await db.commit()
        print('Updated Ollama to llama3:latest')
            
if __name__ == "__main__":
    asyncio.run(update_model())
