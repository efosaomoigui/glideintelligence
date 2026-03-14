import asyncio
from sqlalchemy import text, select
from app.database import AsyncSessionLocal
from app.workers.tasks import fetch_articles_job, normalize_articles_job, clustering_job, ai_analysis_job

async def manual_trigger():
    async with AsyncSessionLocal() as db:
        # Check providers
        from app.models.settings import AIProvider
        res = await db.execute(select(AIProvider).where(AIProvider.enabled == True))
        providers = res.scalars().all()
        print("\nEnabled AI Providers:")
        for p in providers:
            print(f" - {p.name}: {p.model} (Priority: {p.priority})")

        # Check sources
        from app.models.source import Source
        result = await db.execute(select(Source).where(Source.is_active == True))
        sources = result.scalars().all()
        print(f"\nActive sources found: {len(sources)}")
        for s in sources:
            print(f" - {s.name}: {s.url}")
        
        if not sources:
            print("WARNING: No active sources found. Ingestion will NOT run.")
            return

        print("\nTriggering fetch_articles_job logic...")
        from app.services.crawler_service import CrawlerService
        crawler = CrawlerService(db)
        total_fetched = 0
        for s in sources:
            try:
                print(f"Fetching from {s.name}...")
                count = await crawler.fetch_articles(s)
                total_fetched += count
                print(f"Fetched {count} articles.")
            except Exception as e:
                print(f"Error fetching from {s.name}: {e}")

        print(f"\nTotal articles fetched: {total_fetched}")
        
        if total_fetched > 0:
            print("\nTriggering normalize & clustering logic...")
            from app.workers.tasks import normalize_articles_job, clustering_job
            
            # Since these use run_async internally, we call them
            normalize_articles_job()
            clustering_job()
            
            # Verify counts
            res_art = await db.execute(text("SELECT COUNT(*) FROM raw_articles"))
            res_top = await db.execute(text("SELECT COUNT(*) FROM topics"))
            print(f"\nSummary counts in DB:")
            print(f" - Articles: {res_art.scalar()}")
            print(f" - Topics: {res_top.scalar()}")
        else:
            print("No new articles to process.")

if __name__ == "__main__":
    asyncio.run(manual_trigger())
