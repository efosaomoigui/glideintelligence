import asyncio
from sqlalchemy import text
from app.database import engine

async def check_locks():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT pid, usename, pg_blocking_pids(pid) as blocked_by, query, state, wait_event_type, wait_event
            FROM pg_stat_activity
            WHERE state != 'idle';
        """))
        rows = result.fetchall()
        print(f"{'PID':<10} | {'Blocked By':<15} | {'State':<15} | {'Query'}")
        print("-" * 100)
        for row in rows:
            print(f"{row[0]:<10} | {str(row[2]):<15} | {row[4]:<15} | {row[3][:100]}")

if __name__ == "__main__":
    asyncio.run(check_locks())
