import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def check_locks():
    print("Checking active queries and locks...")
    async for session in get_db():
        try:
            query = text("""
                SELECT pid, state, query_start, query 
                FROM pg_stat_activity 
                WHERE state != 'idle' AND pid != pg_backend_pid();
            """)
            result = (await session.execute(query)).all()
            
            if not result:
                print("No active queries found.")
            else:
                print(f"Found {len(result)} active queries:")
                for row in result:
                    print(f"PID: {row.pid}, State: {row.state}, Start: {row.query_start}")
                    print(f"Query: {row.query}")
                    print("-" * 40)
                    
            # Check specifically for locks
            lock_query = text("""
                SELECT t.relname, l.locktype, l.page, l.virtualtransaction, l.pid, l.mode, l.granted
                FROM pg_locks l
                JOIN pg_class t ON l.relation = t.oid
                WHERE t.relname = 'topics' AND l.locktype = 'relation';
            """)
            locks = (await session.execute(lock_query)).all()
            if locks:
                print(f"\nFound {len(locks)} locks on 'topics' table:")
                for lock in locks:
                     print(f"PID: {lock.pid}, Mode: {lock.mode}, Granted: {lock.granted}")
                     # if lock.pid != session.bind.pool.connect().info['backend_pid']: 
                     print(f"Terminating PID {lock.pid}...")
                     try:
                         # Use pg_terminate_backend
                         await session.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": lock.pid})
                         await session.commit()
                         print(f"Terminated {lock.pid}")
                     except Exception as kille:
                         print(f"Failed to kill {lock.pid}: {kille}")

        except Exception as e:
            print(f"Error checking locks: {e}")
            import traceback
            traceback.print_exc()
        return # finish

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_locks())
