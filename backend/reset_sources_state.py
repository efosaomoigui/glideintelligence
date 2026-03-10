import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def reset_sources():
    async with AsyncSessionLocal() as session:
        print("Resetting source fetch state...")
        try:
            r1 = await session.execute(
                text("UPDATE sources SET last_fetched_at = NULL, fetch_error_count = 0")
            )
            r2 = await session.execute(text("DELETE FROM source_health"))
            await session.commit()
            print(f"  [OK] sources reset          ({r1.rowcount} rows)")
            print(f"  [OK] source_health cleared  ({r2.rowcount} rows)")
        except Exception as e:
            await session.rollback()
            print(f"  [!!] Source reset failed: {e}")

if __name__ == "__main__":
    asyncio.run(reset_sources())
