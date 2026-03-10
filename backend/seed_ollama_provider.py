"""
Seed Ollama AI Provider to Database
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.settings import AIProvider, AIProviderType
from sqlalchemy import select

async def seed_ollama():
    async with AsyncSessionLocal() as db:
        # Check if Ollama provider already exists
        result = await db.execute(
            select(AIProvider).where(AIProvider.name == "Ollama")
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Ollama provider already exists with priority {existing.priority}")
            print("Updating configuration...")
            existing.model = "llama3.2"
            existing.enabled = True
            existing.priority = 8
            existing.type = AIProviderType.OPEN_SOURCE
        else:
            print("Creating new Ollama provider...")
            ollama = AIProvider(
                name="Ollama",
                type=AIProviderType.OPEN_SOURCE,
                model="llama3.2",
                api_key=None,  # Not needed for Ollama
                enabled=True,
                priority=8  # Between BART (5) and Gemini (10)
            )
            db.add(ollama)
        
        await db.commit()
        
        # Show all providers
        result = await db.execute(
            select(AIProvider).order_by(AIProvider.priority.desc())
        )
        providers = result.scalars().all()
        
        print("\n" + "="*60)
        print("AI Providers Configuration:")
        print("="*60)
        for p in providers:
            status = "[ENABLED]" if p.enabled else "[DISABLED]"
            print(f"{status} {p.name}")
            print(f"  Model: {p.model}")
            print(f"  Priority: {p.priority}")
            print(f"  Type: {p.type}")
            print()
        
        print("="*60)
        print("Provider Priority Order (highest first):")
        print("="*60)
        for p in providers:
            if p.enabled:
                print(f"  {p.priority}: {p.name} ({p.model})")
        print()
        print("Ollama provider configured successfully!")
        print("\nNext steps:")
        print("1. Start Docker containers: docker-compose up -d")
        print("2. Pull LLaMA model: docker exec -it ollama ollama pull llama3.2:3b-instruct")
        print("3. Test provider: python test_ollama_provider.py")

if __name__ == "__main__":
    asyncio.run(seed_ollama())
