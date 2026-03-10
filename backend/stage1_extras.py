import asyncio, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(".env")
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def run():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT COUNT(*) FROM raw_articles WHERE content ~ '<[^>]+'"))
        print("HTML residue total:", r.scalar())
        r2 = await s.execute(text("SELECT id, SUBSTRING(content,1,80) FROM raw_articles WHERE content IS NOT NULL AND LENGTH(TRIM(content)) < 100"))
        for row in r2.fetchall():
            print(f"Truncated id={row[0]} | content: {row[1]}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
