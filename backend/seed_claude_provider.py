"""
seed_claude_provider.py

Adds Claude (claude-3-5-haiku-20241022) as the PRIMARY AI provider.
Sets priority=20 (highest). Disables all other providers.
Reads API key from ANTHROPIC_API_KEY in .env via settings.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.settings import AIProvider, AIProviderType


CLAUDE_MODEL = "claude-3-haiku-20240307"


async def seed_claude():
    print("")
    print("=" * 60)
    print("  GLIDE INTELLIGENCE - SEED CLAUDE AI PROVIDER")
    print("=" * 60)

    api_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  [!!] ERROR: ANTHROPIC_API_KEY not set in .env / environment!")
        print("       Add:  ANTHROPIC_API_KEY=sk-ant-...")
        return

    print(f"\n  [OK] API key found: {api_key[:20]}...{api_key[-6:]}")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:

        # 1. Disable ALL existing providers
        print("\n[1/3] Disabling all existing providers...")
        result = await session.execute(select(AIProvider))
        existing = result.scalars().all()

        for p in existing:
            p.enabled = False
            print(f"  [--] Disabled: {p.name} ({p.model})")

        await session.commit()

        # 2. Upsert Claude
        print("\n[2/3] Upserting Claude provider...")
        stmt = select(AIProvider).where(AIProvider.name == "Claude")
        result = await session.execute(stmt)
        claude = result.scalar_one_or_none()

        if claude:
            claude.api_key = api_key
            claude.model = CLAUDE_MODEL
            claude.enabled = True
            claude.priority = 20
            claude.type = AIProviderType.PAID
            print(f"  [OK] Updated existing Claude: priority=20, enabled=True")
        else:
            claude = AIProvider(
                name="Claude",
                type=AIProviderType.PAID,
                api_key=api_key,
                model=CLAUDE_MODEL,
                enabled=True,
                priority=20,
            )
            session.add(claude)
            print(f"  [OK] Created new Claude: model={CLAUDE_MODEL}, priority=20")

        await session.commit()

        # 3. Print final state
        print("\n[3/3] Final AI Provider State:")
        print(f"  {'Name':<20} {'Model':<35} {'Enabled':<10} {'Priority'}")
        print(f"  {'-'*20} {'-'*35} {'-'*10} {'-'*8}")
        result = await session.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
        providers = result.scalars().all()
        for p in providers:
            status = "[ACTIVE]" if p.enabled else "[off]   "
            print(f"  {p.name:<20} {p.model:<35} {status:<10} {p.priority}")

    await engine.dispose()
    print("")
    print("=" * 60)
    print("  CLAUDE IS NOW THE PRIMARY AI PROVIDER.")
    print("  Run your pipeline - it will use Claude for all analysis.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_claude())
