import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.settings import AIProvider, AIProviderType, FeatureFlag
from app.models.source import Source, SourceHealth

async def seed_governance():
    async with AsyncSessionLocal() as db:
        # 1. Seed AI Providers
        providers = [
            AIProvider(name="OpenAI GPT-4", type=AIProviderType.PAID, model="gpt-4", priority=100, enabled=True),
            AIProvider(name="Anthropic Claude 3", type=AIProviderType.PAID, model="claude-3-opus", priority=90, enabled=True),
            AIProvider(name="Local Ollama (Llama 3)", type=AIProviderType.OPEN_SOURCE, model="llama3", priority=50, enabled=True)
        ]
        
        for p in providers:
            result = await db.execute(select(AIProvider).where(AIProvider.name == p.name))
            if not result.scalar_one_or_none():
                db.add(p)
        
        # 2. Seed Feature Flags
        flags = [
            FeatureFlag(key="CRAWLER", enabled=True),
            FeatureFlag(key="AI_NORMALIZATION", enabled=True),
            FeatureFlag(key="VIDEO_FETCH", enabled=False),
            FeatureFlag(key="PREMIUM_INSIGHTS", enabled=True)
        ]
        
        for f in flags:
            result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == f.key))
            if not result.scalar_one_or_none():
                db.add(f)
        
        # 3. Seed Source Health for existing sources
        res = await db.execute(select(Source))
        sources = res.scalars().all()
        for s in sources:
            h_res = await db.execute(select(SourceHealth).where(SourceHealth.source_id == s.id))
            if not h_res.scalar_one_or_none():
                db.add(SourceHealth(source_id=s.id, status="healthy"))
        
        await db.commit()
        print("Governance data seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_governance())
