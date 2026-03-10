import asyncio
import logging
import sys

# Configure logging to stdout so Docker can capture it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("completeness_agent")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Import the centralized database dependencies
from app.database import AsyncSessionLocal
from app.models.topic import Topic, TopicAnalysis
from app.utils.jobs import create_job_record, update_job_status

def is_valid_analysis(analysis: TopicAnalysis) -> bool:
    """
    Verifies intelligence integrity with 'Soft Validation'.
    - Mandatory: executive_summary
    - Optional: list fields (warn if empty but don't fail)
    """
    if not analysis:
        logger.warning("No TopicAnalysis record found.")
        return False
        
    # Check Executive Summary (STRICT)
    if not analysis.executive_summary or len(analysis.executive_summary.strip()) < 15:
        logger.warning(f"CRITICAL: executive_summary is missing or too short.")
        return False
        
    # Check List Fields (SOFT)
    # We now allow topics to pass even if some fields are missing, 
    # as long as the core narrative (executive_summary) is strong.
    list_fields = [
        ('what_you_need_to_know', analysis.what_you_need_to_know),
        ('key_takeaways', analysis.key_takeaways),
        ('drivers_of_story', analysis.drivers_of_story),
        ('strategic_implications', analysis.strategic_implications)
    ]
    
    missing_count = 0
    for field_name, val in list_fields:
        if not val or not isinstance(val, list) or len(val) == 0:
            logger.info(f"SOFT WARN: {field_name} is empty.")
            missing_count += 1
                
    # If more than 2 list fields are missing, it's considered poor quality
    if missing_count > 2:
        logger.warning(f"Topic failed soft validation (missing {missing_count} fields).")
        return False
        
    # Confidence Score (SOFT)
    if analysis.confidence_score is None or analysis.confidence_score < 0.3:
        logger.warning(f"Low confidence score: {analysis.confidence_score}")
        # We still allow it to pass if the summary is long enough
        if len(analysis.executive_summary) < 100:
            return False
        
    return True

async def verify_next_topic(session: AsyncSession) -> bool:
    """
    Fetches the next 'complete' topic and verifies its analysis data.
    Uses FOR UPDATE SKIP LOCKED to ensure safe concurrent processing.
    """
    try:
        logger.info("Checking for completed topics to verify...")
        
        # Select 1 topic that is marked 'complete'
        query = (
            select(Topic)
            .options(selectinload(Topic.analysis))
            .where(Topic.analysis_status == 'complete')
            .order_by(Topic.updated_at.desc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        
        result = await session.execute(query)
        topic = result.scalar_one_or_none()
        
        if not topic:
            return False
            
        logger.info(f"🔍 Locked Topic {topic.id} for Completeness Verification: '{topic.title}'")
        
        # Create Job record
        job_id = await create_job_record(session, "COMPLETENESS_AGENT", payload={"topic_id": topic.id, "title": topic.title})
        await update_job_status(session, job_id, "RUNNING")
        
        # Commit job creation
        await session.commit()
        
        # Verify the fields
        is_valid = is_valid_analysis(topic.analysis)
        
        if is_valid:
            logger.info(f"✅ Topic {topic.id} passed completeness check! Marking as 'verified'.")
            topic.analysis_status = 'verified'
            await update_job_status(session, job_id, "SUCCESS", result={"topic_id": topic.id, "status": "verified"})
        else:
            logger.warning(f"❌ Topic {topic.id} failed completeness check! Resetting to 'pending'.")
            topic.analysis_status = 'pending'
            await update_job_status(session, job_id, "FAILED", error="Validation failed: missing or truncated fields")
            # Clear out the bad data to force a totally fresh run
            if topic.analysis:
               topic.analysis.executive_summary = ""
               topic.analysis.what_you_need_to_know = []
               topic.analysis.key_takeaways = []
               topic.analysis.drivers_of_story = []
               topic.analysis.strategic_implications = []
               topic.analysis.regional_impact = []
               topic.analysis.confidence_score = 0.0
        
        session.add(topic)
        await session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during completeness validation: {e}")
        try:
            if 'job_id' in locals():
                await update_job_status(session, job_id, "FAILED", error=str(e))
        except:
            pass
        return False

async def worker_loop():
    """Continuously poll the database for completed topics to verify."""
    logger.info("🛡️ Starting Completeness Agent worker loop...")
    
    while True:
        try:
            async with AsyncSessionLocal() as session:
                processed_something = await verify_next_topic(session)
                
            if not processed_something:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Critical error in completeness worker loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Completeness Agent shutting down.")
