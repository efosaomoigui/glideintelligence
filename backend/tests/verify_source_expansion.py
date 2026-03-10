
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from app.models.source import Source, SourceType, SourceCategory
from sqlalchemy import select, delete

async def verify_source_expansion():
    async with AsyncSessionLocal() as db:
        print("Verifying Source Expansion...")
        
        # 1. Cleanup previous test run
        await db.execute(delete(Source).where(Source.name == "Test Gov Source"))
        await db.commit()
        
        # 2. Create a Source with new fields
        new_source = Source(
            name="Test Gov Source",
            url="https://gov.test",
            domain="gov.test",
            type=SourceType.SOCIAL,
            category=SourceCategory.GOVERNMENT,
            api_key="secret_key_123",
            is_active=True
        )
        db.add(new_source)
        await db.commit()
        await db.refresh(new_source)
        
        # 3. Verify it was saved correctly
        result = await db.execute(select(Source).where(Source.name == "Test Gov Source"))
        saved_source = result.scalar_one()
        
        print(f"Source Created: {saved_source.name}")
        print(f"Type: {saved_source.type} (Expected: {SourceType.SOCIAL})")
        print(f"Category: {saved_source.category} (Expected: {SourceCategory.GOVERNMENT})")
        print(f"API Key: {saved_source.api_key} (Expected: 'secret_key_123')")
        
        assert saved_source.type == SourceType.SOCIAL
        assert saved_source.category == SourceCategory.GOVERNMENT
        assert saved_source.api_key == "secret_key_123"
        
        print("✅ usage verification PASSED")

if __name__ == "__main__":
    asyncio.run(verify_source_expansion())
