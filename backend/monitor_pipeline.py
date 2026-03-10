import asyncio
import time
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def monitor():
    print("Monitoring Pipeline Progress (Ctrl+C to stop)...")
    print(f"{'Time':<10} | {'Articles':<10} | {'Embeds':<10} | {'Topics':<10} | {'Analysis':<10} | {'Trends':<10}")
    print("-" * 70)
    
    async with AsyncSessionLocal() as session:
        while True:
            try:
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
                
                timestamp = time.strftime("%H:%M:%S")
                print(f"{timestamp:<10} | {articles:<10} | {embeds:<10} | {topics:<10} | {analysis:<10} | {trends:<10}")
                
            except Exception as e:
                print(f"Error: {e}")
                
            await asyncio.sleep(5)

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("\nStopped.")
