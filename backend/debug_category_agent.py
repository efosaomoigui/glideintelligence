import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text, select
from app.models.topic import Topic
from app.utils.jobs import update_job_status

async def check():
    async with AsyncSessionLocal() as db:
        # Check recent jobs
        print("--- Recent Category Agent Jobs ---")
        result = await db.execute(text("SELECT id, status, result, error, created_at FROM jobs WHERE type = 'CATEGORY_AGENT' ORDER BY created_at DESC LIMIT 10;"))
        jobs = result.fetchall()
        for j in jobs:
            print(f"Job {j[0]}: {j[1]} | Error: {j[3]} | Time: {j[4]}")
        
        # Check topics in 'verified' status
        result = await db.execute(text("SELECT count(*) FROM topics WHERE analysis_status = 'verified';"))
        count = result.scalar()
        print(f"\nTopics with status 'verified': {count}")
        
        # Check topics in other statuses
        result = await db.execute(text("SELECT analysis_status, count(*) FROM topics GROUP BY analysis_status;"))
        stats = result.fetchall()
        print("\nTopic Status breakdown:")
        for s in stats:
            print(f"  {s[0]}: {s[1]}")
            
        # Check feature flag
        result = await db.execute(text("SELECT key, enabled FROM feature_flags WHERE key = 'agent_category_paused';"))
        flag = result.fetchone()
        print(f"\nPause Flag: {flag[1] if flag else 'Not Set'}")
        
        # Check AI Providers
        print("\n--- AI Providers Status ---")
        result = await db.execute(text("SELECT name, type, enabled, priority FROM ai_providers ORDER BY priority ASC;"))
        providers = result.fetchall()
        for p in providers:
            print(f"  {p[0]} ({p[1]}): Enabled={p[2]}, Priority={p[3]}")

if __name__ == "__main__":
    asyncio.run(check())
