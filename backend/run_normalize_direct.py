import asyncio
import sys
import os

# Add backend to path so imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.workers.tasks import normalize_articles_job

async def run_job_directly():
    print("Running normalize_articles_job directly...")
    try:
        # calling .apply() or calling the function directly if it wasn't wrapped in shared_task 
        # but since it is wrapped, we can try importing the underlying function or just calling it if celery allows
        
        # In newer celery, calling the decorated function directly works and executes synchronously if not configured otherwise
        # but normalize_articles_job is an asyncio wrapper effectively.
        
        # It returns a dict or coroutine.
        # Let's try calling it.
        res = normalize_articles_job(job_id=None)
        print(f"Result: {res}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_job_directly())
