
import asyncio
from app.database import AsyncSessionLocal
from app.models.topic import Topic
from sqlalchemy import select, text
import sys
import os

sys.path.append(os.getcwd())

async def check_failed_topics():
    async with AsyncSessionLocal() as db:
        print("\nChecking for failed topics...")
        # Check for analysis_failed status
        query = select(Topic).where(Topic.status == 'analysis_failed')
        result = await db.execute(query)
        failed_topics = result.scalars().all()
        
        print(f"Docs found with status='analysis_failed': {len(failed_topics)}")
        for t in failed_topics:
            err = t.metadata_.get('last_error', 'N/A') if t.metadata_ else 'N/A'
            print(f"  ID: {t.id} | Title: {t.title[:30]}... | Status: {t.status} | Last Error: {err[:50]}")

        # Check for error sentiment
        query2 = select(Topic).where(Topic.overall_sentiment == 'error')
        result2 = await db.execute(query2)
        error_sentiment = result2.scalars().all()
        print(f"\nDocs found with overall_sentiment='error': {len(error_sentiment)}")
        for t in error_sentiment:
             print(f"  ID: {t.id} | Title: {t.title[:30]}... | Sentiment: {t.overall_sentiment}")

if __name__ == "__main__":
    asyncio.run(check_failed_topics())
