import asyncio
import sys
import os

backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_db():
    async with AsyncSessionLocal() as s:
        p = await s.execute(text("SELECT question FROM polls LIMIT 1"))
        poll = p.first()
        if poll:
            print("Successfully generated Contextual Poll:")
            print(poll.question)
        else:
            print("No polls found")

if __name__ == "__main__":
    asyncio.run(check_db())
