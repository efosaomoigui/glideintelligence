import asyncio
import os
import sys
import time

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings as app_settings
from app.models import RawArticle, ArticleEmbedding, Topic, TopicAnalysis, AISummary, TopicTrend
from app.workers.celery_app import celery_app # Ensure config is loaded
from app.workers.tasks import fetch_articles_job, normalize_articles_job, clustering_job, ai_analysis_job, trend_update_job

async def verify_pipeline():
    print(f"Connecting to DB: {app_settings.DATABASE_URL}...")
    engine = create_async_engine(app_settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Fetch Articles
        print("\n--- Step 1: Ingestion ---")
        initial_count = (await session.execute(select(func.count(RawArticle.id)))).scalar()
        print(f"Initial Article Count: {initial_count}")
        
        print("Triggering fetch_articles_job...")
        try:
            # Trigger via Celery (assuming worker is running or eager mode)
            # If no worker, this will just queue. 
            # For verification without worker, we might need to force execution.
            # But let's try triggering and monitoring.
            task = fetch_articles_job.delay() 
            print(f"Task ID: {task.id}")
        except Exception as e:
            print(f"Failed to trigger task: {e}")
            # Fallback: Try running directly if configured (but tasks.py is async wrapped)
            pass

        # Wait loop
        for i in range(30):
            await asyncio.sleep(2)
            current_count = (await session.execute(select(func.count(RawArticle.id)))).scalar()
            if current_count > initial_count:
                print(f"Success! New Articles Found: {current_count - initial_count}")
                break
            print(f"Waiting for articles... ({i+1}/30)")
        else:
            print("Warning: No new articles fetched.")
            # Verify if we have ANY data to proceed
            total_count = (await session.execute(select(func.count(RawArticle.id)))).scalar()
            if total_count == 0:
                print("Error: No articles in database. Cannot proceed.")
                return
            print(f"Proceeding with {total_count} existing articles.")

        # 2. Normalize
        print("\n--- Step 2: Normalization ---")
        print("Triggering normalize_articles_job...")
        normalize_articles_job.delay()
        
        for i in range(30):
            await asyncio.sleep(2)
            emb_count = (await session.execute(select(func.count(ArticleEmbedding.id)))).scalar()
            if emb_count > 0:
                 print(f"Success! Article Embeddings Generated: {emb_count}")
                 break
            print(f"Waiting for embeddings... ({i+1}/30)")
            
        # 3. Clustering
        print("\n--- Step 3: Clustering ---")
        print("Triggering clustering_job...")
        clustering_job.delay()
        
        for i in range(30):
            await asyncio.sleep(2)
            topic_count = (await session.execute(select(func.count(Topic.id)))).scalar()
            if topic_count > 0:
                 print(f"Success! Topics Created: {topic_count}")
                 break
            print(f"Waiting for topics... ({i+1}/30)")

        # 4. AI Analysis
        print("\n--- Step 4: AI Analysis ---")
        print("Triggering ai_analysis_job...")
        ai_analysis_job.delay()
        
        for i in range(30):
            await asyncio.sleep(2)
            analysis_count = (await session.execute(select(func.count(TopicAnalysis.id)))).scalar()
            summary_count = (await session.execute(select(func.count(AISummary.id)))).scalar()
            if analysis_count > 0:
                 print(f"Success! Topic Analyses: {analysis_count}, Summaries: {summary_count}")
                 break
            print(f"Waiting for analysis... ({i+1}/30)")

        # 5. Trends
        print("\n--- Step 5: Trend Updates ---")
        print("Triggering trend_update_job...")
        trend_update_job.delay()
        
        for i in range(15):
            await asyncio.sleep(2)
            trend_count = (await session.execute(select(func.count(TopicTrend.id)))).scalar()
            if trend_count > 0:
                 print(f"Success! Trend Data Points: {trend_count}")
                 break
            print(f"Waiting for trends... ({i+1}/15)")

    await engine.dispose()
    print("\nPipeline Verification Complete!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_pipeline())
