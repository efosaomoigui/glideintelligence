import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv()

from app.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT id, title, content FROM raw_articles WHERE id = 7"))
        row = result.first()
        if row:
            print(f"ID: {row.id}")
            print(f"Title: {row.title}")
            print("--- Content Start ---")
            print(row.content[:500]) # First 500 chars
            print("--- Content End ---")
        else:
            print("Article 7 not found.")

if __name__ == "__main__":
    load_dotenv()
    try:
        asyncio.run(main())
    except ImportError:
        # Fallback if specific app import fails due to path
        print("Could not import app.database. Ensure you are running from project root.")
