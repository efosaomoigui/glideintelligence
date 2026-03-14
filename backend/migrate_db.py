import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate_published_at():
    async with engine.connect() as conn:
        print("Migrating published_at from VARCHAR to TIMESTAMP...")
        
        # 1. Clear existing data in raw_articles to avoid conversion errors if any invalid strings remain
        # (User said they cleaned data, but let's be safe)
        await conn.execute(text("TRUNCATE TABLE raw_articles CASCADE;"))
        
        # 2. Alter column type
        await conn.execute(text("""
            ALTER TABLE raw_articles 
            ALTER COLUMN published_at TYPE TIMESTAMP WITH TIME ZONE 
            USING published_at::TIMESTAMP WITH TIME ZONE;
        """))
        
        await conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_published_at())
