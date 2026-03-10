"""
Script to enable Ollama as an AI provider in the database.
This adds Ollama/Llama3 as a fallback provider when cloud providers fail.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
load_dotenv()

from app.database import AsyncSessionLocal
from app.models.settings import AIProvider, AIProviderType
from sqlalchemy import select


async def enable_ollama_provider():
    """Enable Ollama provider in the database."""
    async with AsyncSessionLocal() as db:
        # Check if Ollama provider already exists
        result = await db.execute(
            select(AIProvider).where(AIProvider.name == "Ollama")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"[INFO] Ollama provider already exists (ID: {existing.id})")
            print(f"  Enabled: {existing.enabled}")
            print(f"  Priority: {existing.priority}")
            print(f"  Model: {existing.model}")
            
            # Update to ensure it's enabled
            existing.enabled = True
            existing.priority = 1  # Lower priority than cloud providers
            existing.model = "tinyllama:latest"
            await db.commit()
            print("[OK] Updated Ollama provider settings")
        else:
            # Create new Ollama provider
            ollama_provider = AIProvider(
                name="Ollama",
                type=AIProviderType.LOCAL,
                api_key="",  # No API key needed for local
                model="llama3:latest",
                enabled=True,
                priority=1  # Lower priority - used as fallback
            )
            db.add(ollama_provider)
            await db.commit()
            print("[OK] Created and enabled Ollama provider")
            print(f"  ID: {ollama_provider.id}")
            print(f"  Model: {ollama_provider.model}")
            print(f"  Priority: {ollama_provider.priority}")
        
        # Show all enabled providers
        print("\n" + "="*60)
        print("ALL ENABLED AI PROVIDERS (ordered by priority):")
        print("="*60)
        
        result = await db.execute(
            select(AIProvider)
            .where(AIProvider.enabled == True)
            .order_by(AIProvider.priority.desc())
        )
        providers = result.scalars().all()
        
        for p in providers:
            print(f"{p.priority}. {p.name} ({p.model}) - Type: {p.type}")
        
        print("\nProvider fallback order: " + " -> ".join([p.name for p in providers]))


if __name__ == "__main__":
    asyncio.run(enable_ollama_provider())
