import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.source import Source
from app.models.article import RawArticle

async def seed_data():
    async with AsyncSessionLocal() as db:
        # 1. Create a test source if it doesn't exist
        result = await db.execute(select(Source).where(Source.name == "Global News Network"))
        source = result.scalar_one_or_none()
        
        if not source:
            source = Source(
                name="Global News Network",
                url="https://globalnews.example.com",
                domain="globalnews.example.com",
                reliability_score=0.85,
                bias_rating=0.0
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
            print(f"Created source: {source.name}")
        else:
            print(f"Source already exists: {source.name}")

        # 2. Add some raw articles
        articles_to_add = [
            {
                "external_id": "gnn-001",
                "url": "https://globalnews.example.com/tech-breakthrough",
                "title": "Quantum Computing Breakthrough in Silicon Valley",
                "content": "Researchers have achieved a major milestone in quantum computing, demonstrating a new way to stabilize qubits at room temperature. This discovery could pave the way for more accessible quantum processors.",
                "description": "A major milestone in quantum computing research.",
                "author": "Jane Doe"
            },
            {
                "external_id": "gnn-002",
                "url": "https://globalnews.example.com/climate-summit",
                "title": "Global Leaders Meet for Climate Summit in Paris",
                "content": "World leaders gathered today for a high-stakes climate summit, aiming to reach new agreements on carbon emission reductions and sustainable energy investment.",
                "description": "Climate summit highlights sustainability goals.",
                "author": "John Smith"
            },
            {
                "external_id": "gnn-003",
                "url": "https://globalnews.example.com/ai-regulation",
                "title": "EU Proposes New Regulations for Artificial Intelligence",
                "content": "The European Union has unveiled a comprehensive framework for AI regulation, focusing on transparency, safety, and ethical considerations for high-risk applications.",
                "description": "New EU framework for AI ethics and safety.",
                "author": "Alice Brown"
            }
        ]

        for art_data in articles_to_add:
            result = await db.execute(select(RawArticle).where(RawArticle.url == art_data["url"]))
            if not result.scalar_one_or_none():
                article = RawArticle(
                    source_id=source.id,
                    **art_data
                )
                db.add(article)
                print(f"Adding article: {article.title}")
        
        await db.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
