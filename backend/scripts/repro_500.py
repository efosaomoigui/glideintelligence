import asyncio
import sys
import os

# Add backend directory to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.services.news_service import NewsService

async def main():
    async with AsyncSessionLocal() as db:
        service = NewsService(db)
        print("Calling get_trending_topics...")
        try:
            items, total = await service.get_trending_topics(filter_type="today")
            print(f"Success! Got {len(items)} items, total {total}")
        except Exception as e:
            print(f"Caught expected error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
