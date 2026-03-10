"""
Test AI analysis job with a specific topic
"""
import asyncio
from app.workers.tasks import ai_analysis_job

def test_ai_analysis():
    print("Testing AI analysis job...")
    print("Topic ID: 7 (economic category)")
    print("\nThis may take 30-60 seconds...\n")
    
    try:
        # Run the job directly (not via Celery)
        result = ai_analysis_job(topic_id=7)
        print(f"\n[SUCCESS] Job completed: {result}")
    except Exception as e:
        print(f"\n[ERROR] Job failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analysis()
