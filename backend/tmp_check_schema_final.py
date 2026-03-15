import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        # Check column
        result = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'topic_analysis' AND column_name = 'social_keywords';"))
        col_exists = result.fetchone() is not None
        print(f"Column 'social_keywords' exists in 'topic_analysis': {col_exists}")
        
        # Check table
        result = await db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'topic_social_reactions';"))
        table_exists = result.fetchone() is not None
        print(f"Table 'topic_social_reactions' exists: {table_exists}")

if __name__ == "__main__":
    asyncio.run(check())
