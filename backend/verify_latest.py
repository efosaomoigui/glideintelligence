import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from app.config import settings
from app.models.topic import Topic, TopicAnalysis
from app.models.ai_usage import AIUsageLog

async def verify_latest_analysis():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check latest AI Usage
        result = await session.execute(
            select(AIUsageLog)
            .order_by(AIUsageLog.timestamp.desc())
            .limit(5)
        )
        logs = result.scalars().all()
        print("\n--- Latest AI Usage Logs ---")
        for log in logs:
            print(f"Provider: {log.provider_name} | Model: {log.model_name} | Created: {log.timestamp}")

        # Check latest Analysis
        result = await session.execute(
            select(TopicAnalysis)
            .order_by(TopicAnalysis.updated_at.desc())
            .limit(1)
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            print("\n--- Latest Topic Analysis ---")
            print(f"Topic ID: {analysis.topic_id}")
            print(f"Summary (first 100 chars): {analysis.summary[:100]}...")
            print(f"Key Takeaways: {analysis.key_takeaways}")
            print(f"Drivers: {analysis.drivers_of_story}")
        else:
            print("No analysis found.")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_latest_analysis())
