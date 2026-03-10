"""
tmp_check_providers.py - diagnose AI providers
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.settings import AIProvider
import logging
logging.basicConfig(level=logging.WARNING)

async def run():
    async with AsyncSessionLocal() as s:
        r = await s.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
        rows = r.scalars().all()
        print("\n=== AI Providers ===")
        for p in rows:
            key_preview = (str(p.api_key) or "")[:25] + "..." if p.api_key else "--- EMPTY ---"
            print(f"  id={p.id} | {p.name} | model={p.model} | enabled={p.enabled} | priority={p.priority}")
            print(f"    api_key: {key_preview}")

        # Test Claude service directly
        print("\n=== Testing ClaudeService init ===")
        from app.services.ai.claude_service import ClaudeService
        claude = ClaudeService()
        print(f"  ClaudeService available: {claude.is_available()}")

if __name__ == "__main__":
    asyncio.run(run())
