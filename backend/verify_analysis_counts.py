import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check_analysis_counts():
    tables = [
        'topics', 
        'topic_analysis', 
        'source_perspectives', 
        'regional_impacts', 
        'intelligence_cards', 
        'topic_sentiment_breakdown', 
        'ai_summaries'
    ]
    async with AsyncSessionLocal() as session:
        print("\n--- AI Analysis Record Counts ---")
        for table in tables:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"{table:25}: {count}")
            except Exception as e:
                print(f"{table:25}: Error - {e}")
        print("---------------------------------\n")

if __name__ == "__main__":
    asyncio.run(check_analysis_counts())
