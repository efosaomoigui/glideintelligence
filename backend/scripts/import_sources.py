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
from app.models.source import SourceType, SourceCategory

async def import_sources():
    # Check multiple possible locations for the dump file
    possible_paths = [
        "sources_dump.json",
        "/app/sources_dump.json",
        os.path.join(os.path.dirname(__file__), "..", "sources_dump.json"),
        os.path.join(os.path.dirname(__file__), "sources_dump.json")
    ]
    
    json_path = None
    for path in possible_paths:
        if os.path.exists(path):
            json_path = path
            break

    if not json_path:
        print(f"Error: sources_dump.json not found. Checked: {possible_paths}")
        print("Please ensure you ran: docker cp backend/sources_dump.json glideintelligence-backend-1:/app/sources_dump.json")
        return

    print(f"Importing sources from {json_path}...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    with open("sources_dump.json", "r") as f:
        data = json.load(f)
        
    async with async_session() as session:
        added = 0
        skipped = 0
        
        for s_data in data:
            # Check if domain already exists
            stmt = select(Source).where(Source.domain == s_data["domain"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Convert string type/category to Enums
                try:
                    s_data["type"] = SourceType(s_data["type"])
                    s_data["category"] = SourceCategory(s_data["category"])
                except Exception:
                    pass # Fallback to raw value if enum mapping fails

                new_source = Source(**s_data)
                session.add(new_source)
                added += 1
            else:
                skipped += 1
                
        await session.commit()
        print(f"Done! Added {added} new sources, skipped {skipped} existing.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(import_sources())
