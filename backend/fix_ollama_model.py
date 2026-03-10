"""
Script to update Ollama provider to use the correct model name.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.models.settings import AIProvider
from sqlalchemy import select


async def fix_ollama_model():
    """Update Ollama provider to use llama3.2:latest."""
    async with AsyncSessionLocal() as db:
        # Find Ollama provider
        result = await db.execute(
            select(AIProvider).where(AIProvider.name == "Ollama")
        )
        ollama = result.scalar_one_or_none()
        
        if ollama:
            print(f"[INFO] Current Ollama model: {ollama.model}")
            ollama.model = "llama3.2:latest"
            await db.commit()
            print(f"[OK] Updated Ollama model to: llama3.2:latest")
        else:
            print("[ERROR] Ollama provider not found")


if __name__ == "__main__":
    asyncio.run(fix_ollama_model())
