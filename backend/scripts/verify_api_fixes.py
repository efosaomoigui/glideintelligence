"""Simple verification of API fixes"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db
from app.services.news_service import NewsService
from app.models import Topic
from sqlalchemy import select

async def verify_fixes():
    """Verify the 3 critical API fixes"""
    print("="*70)
    print("VERIFYING API FIXES")
    print("="*70)
    
    async for db in get_db():
        service = NewsService(db)
        
        # Fix 1: Status filter in get_trending_topics
        print("\n[CHECK 1] Status filter - Only stable topics returned")
        print("-"*70)
        topics, total = await service.get_trending_topics(1, 10, "all", None)
        print(f"Retrieved {len(topics)} topics")
        
        # Check if any non-stable topics
        non_stable = [t for t in topics if hasattr(t, 'status') and t.status != "stable"]
        if len(non_stable) > 0:
            print(f"[FAIL] Found {len(non_stable)} non-stable topics!")
            for t in non_stable:
                print(f"  - Topic {t.id}: status={t.status}")
        else:
            print("[PASS] All topics have status='stable'")
        
        # Fix 2: 404 error handling
        print("\n[CHECK 2] 404 Error handling for non-existent topic")
        print("-"*70)
        try:
            topic = await service.get_topic_detail(99999)
            print("[FAIL] No exception raised for non-existent topic")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print(f"[PASS] HTTPException raised: {e}")
            else:
                print(f"[FAIL] Wrong exception: {e}")
        
        # Fix 3: View count increment
        print("\n[CHECK 3] View count increment")
        print("-"*70)
        # Find a stable topic
        result = await db.execute(
            select(Topic).where(Topic.status == "stable").limit(1)
        )
        test_topic = result.scalar_one_or_none()
        
        if test_topic:
            initial_count = test_topic.view_count
            print(f"Topic {test_topic.id} initial view_count: {initial_count}")
            
            # Call get_topic_detail
            await service.get_topic_detail(test_topic.id)
            
            # Refresh and check
            await db.refresh(test_topic)
            new_count = test_topic.view_count
            print(f"After get_topic_detail: {new_count}")
            
            if new_count > initial_count:
                print(f"[PASS] View count incremented by {new_count - initial_count}")
            else:
                print("[FAIL] View count did not increment")
        else:
            print("[SKIP] No stable topics found for testing")
        
        print("\n" + "="*70)
        print("VERIFICATION COMPLETE")
        print("="*70)

if __name__ == "__main__":
    asyncio.run(verify_fixes())
