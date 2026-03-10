
import sys
import os
import asyncio

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from sqlalchemy import select, text
from app.models.intelligence import CategoryConfig

async def seed_general():
    async with AsyncSessionLocal() as db:
        # Check if politics exists to copy its structure
        res = await db.execute(select(CategoryConfig).where(CategoryConfig.category == 'politics'))
        politics = res.scalar_one_or_none()
        
        # Check if general exists
        res = await db.execute(select(CategoryConfig).where(CategoryConfig.category == 'general'))
        general = res.scalar_one_or_none()
        
        if not general:
            print("Creating 'general' category config...")
            new_config = CategoryConfig(
                category='general',
                dimension_mappings=politics.dimension_mappings if politics else {
                    "primary_dimensions": ["sentiment_pillar", "timeframe", "audience"],
                    "sentiment_pillar_options": ["Public Interest", "Commercial Impact", "Policy Relevance"],
                    "timeframe_options": ["Immediate", "Short-term", "Long-term"],
                    "audience_options": ["General Public", "Specialists", "Decision Makers"]
                },
                impact_categories=politics.impact_categories if politics else [
                    {"key": "economic", "label": "Economy", "icon": "💰"},
                    {"key": "social", "label": "Social", "icon": "👥"},
                    {"key": "political", "label": "Political", "icon": "🏛️"}
                ]
            )
            db.add(new_config)
            await db.commit()
            print("Successfully added 'general' category config.")
        else:
            print("'general' category config already exists.")

if __name__ == "__main__":
    asyncio.run(seed_general())
