import asyncio
import logging
import sys
import os
from sqlalchemy import select, func

# Add the parent directory to sys.path to find 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.topic import Topic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def audit_topic_statuses():
    """Count topics by analysis_status."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Auditing topic statuses...")
            query = select(Topic.analysis_status, func.count(Topic.id)).group_by(Topic.analysis_status)
            result = await session.execute(query)
            counts = result.all()
            
            print("\n" + "="*40)
            print("TOPIC ANALYSIS STATUS DISTRIBUTION")
            print("="*40)
            for status, count in counts:
                print(f"{status:20} | {count:5}")
            print("="*40 + "\n")
            
        except Exception as e:
            logger.error(f"Failed to audit statuses: {e}")

if __name__ == "__main__":
    asyncio.run(audit_topic_statuses())
