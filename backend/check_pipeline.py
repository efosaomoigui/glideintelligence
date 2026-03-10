import asyncio
import time
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_pipeline():
    async with AsyncSessionLocal() as session:
        # Count Articles
        res = await session.execute(text("SELECT COUNT(*) FROM raw_articles"))
        articles = res.scalar()
        
        # Count Embeddings
        res = await session.execute(text("SELECT COUNT(*) FROM article_embeddings"))
        embeds = res.scalar()
        
        # Count Topics
        res = await session.execute(text("SELECT COUNT(*) FROM topics"))
        topics = res.scalar()
        
        # Count Analysis
        res = await session.execute(text("SELECT COUNT(*) FROM topic_analysis"))
        analysis = res.scalar()
        
        # Count Trends
        res = await session.execute(text("SELECT COUNT(*) FROM topic_trends"))
        trends = res.scalar()
        
        print(f"Pipeline Status request at {time.strftime('%H:%M:%S')}:")
        print(f"  Articles: {articles}")
        print(f"  Embeds:   {embeds}")
        print(f"  Topics:   {topics}")
        print(f"  Analysis: {analysis}")
        print(f"  Trends:   {trends}")

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(check_pipeline())
