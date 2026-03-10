import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.topic import Topic
from sqlalchemy import select, update

async def test_sequential_flow():
    print("Starting Sequential Flow Verification...")
    
    # 1. Select or Create a test topic
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Topic).limit(1))
        row = result.scalar_one()
        topic_id = row.id
        topic_title = row.title
        print(f"Testing with Topic ID: {topic_id} - '{topic_title}'")

    # 2. Simulate Pipeline Success
    async with AsyncSessionLocal() as session:
        print("Simulating Pipeline Success...")
        await session.execute(
            update(Topic)
            .where(Topic.id == topic_id)
            .values(analysis_status='pending', status='stable')
        )
        await session.commit()
    
    # Verify enrichment (Standard)
    async with AsyncSessionLocal() as session:
        from app.services.news_service import NewsService
        service = NewsService(session)
        result = await session.execute(select(Topic).where(Topic.id == topic_id))
        topic = result.scalar_one()
        enriched = service._enrich_topic_for_frontend(topic)
        print(f"Initial Enrichment - level: {enriched.intelligence_level}, premium: {enriched.is_premium}")
        
        if enriched.intelligence_level != "Standard" or enriched.is_premium is not False:
            print("Initial enrichment check failed.")
            return

    # 3. Simulate OpenClaw Completion
    async with AsyncSessionLocal() as session:
        print("Simulating OpenClaw Completion...")
        await session.execute(
            update(Topic)
            .where(Topic.id == topic_id)
            .values(analysis_status='complete')
        )
        await session.commit()
    
    # Final re-verify (Premium)
    async with AsyncSessionLocal() as session:
        service = NewsService(session)
        result = await session.execute(select(Topic).where(Topic.id == topic_id))
        topic = result.scalar_one()
        enriched = service._enrich_topic_for_frontend(topic)
        print(f"Final Enrichment - level: {enriched.intelligence_level}, premium: {enriched.is_premium}")
        
        if enriched.intelligence_level != "Premium" or enriched.is_premium is not True:
            print("Final enrichment check failed.")
            return

    print("Success: Sequential Flow Backend Logic Verified!")

if __name__ == "__main__":
    asyncio.run(test_sequential_flow())
