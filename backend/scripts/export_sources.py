import asyncio
import json
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.database import engine
from app.models import Source

async def export_sources():
    print("Exporting local sources...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Source))
        sources = result.scalars().all()
        
        data = []
        for s in sources:
            s_dict = {
                "name": s.name,
                "url": s.url,
                "domain": s.domain,
                "type": s.type.value if hasattr(s.type, 'value') else s.type,
                "category": s.category.value if hasattr(s.category, 'value') else s.category,
                "api_key": s.api_key,
                "reliability_score": float(s.reliability_score) if s.reliability_score is not None else 0.0,
                "bias_rating": float(s.bias_rating) if s.bias_rating is not None else 0.0,
                "is_active": s.is_active,
                "fetch_frequency_minutes": s.fetch_frequency_minutes,
                "logo_url": s.logo_url
            }
            data.append(s_dict)
            
        with open("sources_dump.json", "w") as f:
            json.dump(data, f, indent=2)
            
    print(f"Exported {len(data)} sources to sources_dump.json")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(export_sources())
