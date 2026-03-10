import asyncio
import sys
import os

# Add the current directory to sys.path to allow importing 'app'
sys.path.append(os.getcwd())

from app.database import engine
from app.models.base import Base
from app.models.ai_usage import AIUsageLog

async def create_tables():
    print("Creating database tables...")
    async with engine.begin() as conn:
        # This will create all tables defined in Base that do not exist yet
        await conn.run_sync(Base.metadata.create_all)
    print("AI usage logs table verified/created.")

if __name__ == "__main__":
    asyncio.run(create_tables())
