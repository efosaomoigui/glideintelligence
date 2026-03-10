"""
seed_claude_provider.py

Configures Claude as the PRIMARY AI provider while keeping others as fallback.
Sets Claude with priority=20.
Reads API key from ANTHROPIC_API_KEY in .env.
"""

import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.settings import AIProvider, AIProviderType

# Recommended Claude model
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

async def seed_claude():
    print("")
    print("=" * 60)
    print("  GLIDE INTELLIGENCE - CONFIGURE CLAUDE AI PROVIDER")
    print("=" * 60)

    api_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  [!!] ERROR: ANTHROPIC_API_KEY not set in .env / environment!")
        print("       Please add: ANTHROPIC_API_KEY=your_key_here to backend/.env")
        return

    print(f"\n  [OK] API key found: {api_key[:20]}...{api_key[-6:]}")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Ensure other providers have lower priority (so Claude is primary)
        print("\n[1/3] Adjusting existing provider priorities for failover...")
        result = await session.execute(select(AIProvider).where(AIProvider.name != "Claude"))
        existing = result.scalars().all()

        for p in existing:
            if p.priority >= 20:
                p.priority = 10
                print(f"  [~] Lowered priority for: {p.name} (now {p.priority})")
            p.enabled = True # Ensure failover targets are enabled
        
        await session.commit()

        # 2. Upsert Claude
        print("\n[2/3] Configuring Claude provider...")
        stmt = select(AIProvider).where(AIProvider.name == "Claude")
        result = await session.execute(stmt)
        claude = result.scalar_one_or_none()

        if claude:
            claude.api_key = api_key
            claude.model = CLAUDE_MODEL
            claude.enabled = True
            claude.priority = 20
            claude.type = AIProviderType.PAID
            print(f"  [OK] Updated Claude: priority=20, enabled=True, model={CLAUDE_MODEL}")
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
        print("\n[3/3] Final AI Provider Failover Chain:")
        print(f"  {'Name':<15} {'Model':<30} {'Enabled':<10} {'Priority'}")
        print(f"  {'-'*15} {'-'*30} {'-'*10} {'-'*8}")
        result = await session.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
        providers = result.scalars().all()
        for p in providers:
            status = "[ACTIVE]" if p.enabled else "[off]   "
            print(f"  {p.name:<15} {p.model:<30} {status:<10} {p.priority}")

    await engine.dispose()
    print("\n" + "=" * 60)
    print("  CLAUDE IS NOW PRIMARY. OTHER PROVIDERS ARE FALLBACKS.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_claude())
