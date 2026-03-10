import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workers.tasks import clustering_job

async def run_clustering_direct():
    print("Running clustering_job directly...")
    try:
        # direct call returns coro or dict depending on implementation
        # clustering_job is wrapped by @shared_task
        # In this env, calling it might invoke the wrapper which calls run_async
        res = clustering_job(job_id=None)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # clustering_job wrapper should handle async loop if it uses run_async
    # but let's see. 
    # If tasks.py uses run_async internally, then we just call the function.
    run_clustering_direct() 
    # Wait, run_clustering_direct is async defined above but I am calling it synchronously? 
    # No, I should use asyncio.run if I want to await it, but clustering_job is sync wrapper.
    # So run_clustering_direct doesn't need to be async if it just calls clustering_job
    # actually let's make it sync to avoid confusion.

def run_clustering_sync():
    print("Running clustering_job directly (sync)...")
    try:
        res = clustering_job(job_id=None)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_clustering_sync()
