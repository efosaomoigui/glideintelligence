import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate_published_at_v2():
    async with engine.connect() as conn:
        print("Attempting to alter published_at type...")
        
        # Set a short lock timeout to avoid hanging
        await conn.execute(text("SET lock_timeout = '10s';"))
        
        try:
            # Check if already timestamp
            result = await conn.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'raw_articles' AND column_name = 'published_at';
            """))
            row = result.fetchone()
            if row and row[0] == 'timestamp with time zone':
                print("Column is already TIMESTAMP WITH TIME ZONE. No action needed.")
                return

            # Alter column type directly. 
            # If the user has 'cleaned' the data, this should be fast.
            # We use USING to handle potential conversion issues.
            await conn.execute(text("""
                ALTER TABLE raw_articles 
                ALTER COLUMN published_at TYPE TIMESTAMP WITH TIME ZONE 
                USING CASE 
                    WHEN published_at IS NULL THEN NULL
                    WHEN published_at = '' THEN NULL
                    ELSE published_at::TIMESTAMP WITH TIME ZONE 
                END;
            """))
            
            await conn.commit()
            print("Migration successful: published_at is now TIMESTAMP WITH TIME ZONE.")
        except Exception as e:
            await conn.rollback()
            print(f"Migration failed or timed out: {e}")
            print("The system will continue using string parsing in the service layer as a fallback.")

if __name__ == "__main__":
    asyncio.run(migrate_published_at_v2())
