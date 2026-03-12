import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.database import AsyncSessionLocal
from app.models.topic import Topic
from app.models.region import TopicRegionalCategory
from sqlalchemy import select, delete

async def seed_regional_categorization():
    print("Starting Regional Categorization Seeding")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch all topics that don't have regional categorization yet
            # For simplicity in this script, we'll just update all current active topics
            query = select(Topic).where(Topic.status != 'archived')
            result = await db.execute(query)
            topics = result.scalars().all()
            
            print(f"Found {len(topics)} topics to update")
            
            updated_count = 0
            for topic in topics:
                # Check if already has categories to avoid duplicates if run multiple times
                check_query = select(TopicRegionalCategory).where(TopicRegionalCategory.topic_id == topic.id)
                check_res = await db.execute(check_query)
                if check_res.scalars().first():
                    continue
                
                # Add Nigeria and West Africa as defaults for existing topics
                # In a real scenario, we might want to be more selective, 
                # but user requested to seed existing topics as these.
                db.add(TopicRegionalCategory(
                    topic_id=topic.id,
                    region_name="Nigeria",
                    impact="Neutral"
                ))
                db.add(TopicRegionalCategory(
                    topic_id=topic.id,
                    region_name="West Africa",
                    impact="Neutral"
                ))
                updated_count += 1
            
            await db.commit()
            print(f"Successfully seeded {updated_count} topics with regional tags")
            
        except Exception as e:
            print(f"Error during seeding: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_regional_categorization())
