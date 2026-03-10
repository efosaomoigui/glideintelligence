import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy
from app.config import settings as app_settings
from app.models.base import Base
# Import all models so Base.metadata knows about them
from app.models import *

async def reset_database():
    print(f"Connecting to {app_settings.DATABASE_URL}...")
    engine = create_async_engine(app_settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Dropping all tables...")
        # Drop alembic_version explicitly as it is not in Base.metadata
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS alembic_version"))
        await conn.run_sync(Base.metadata.drop_all)
        print("Tables dropped.")
        
        # We don't necessarily need to create_all if we use alembic, 
        # but dropping ensures alembic upgrade head starts fresh or we can just use create_all
        # Let's just drop. Alembic will manage creation.
        
    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(reset_database())
