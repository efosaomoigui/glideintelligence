import asyncio
from sqlalchemy import text
from app.database import engine

async def kill_blocking_session(pid: int):
    async with engine.connect() as conn:
        print(f"Killing PID {pid} to resolve lock...")
        await conn.execute(text(f"SELECT pg_terminate_backend({pid});"))
        await conn.commit()
        print(f"Session {pid} terminated.")

if __name__ == "__main__":
    import sys
    pid_to_kill = int(sys.argv[1]) if len(sys.argv) > 1 else 170
    asyncio.run(kill_blocking_session(pid_to_kill))
