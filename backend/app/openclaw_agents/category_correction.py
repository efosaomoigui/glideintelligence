import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("category_agent")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Import dependencies
from app.database import AsyncSessionLocal
from app.models.topic import Topic, TopicArticle
from app.models.article import RawArticle
from app.services.ai.content_generator import AIContentGenerator
from app.utils.jobs import create_job_record, update_job_status
from app.constants import VALID_CATEGORIES

async def process_category_correction(session: AsyncSession) -> bool:
    """
    Fetches the next 'verified' topic and corrects its category using AI.
    """
    try:
        logger.info("Checking for verified topics for category correction...")
        
        # 1. Lock and Update Topic to 'verified' (keep analysis_status while working)
        query = (
            select(Topic)
            .where(Topic.analysis_status == 'verified')
            .order_by(Topic.updated_at.desc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        
        result = await session.execute(query)
        topic = result.scalar_one_or_none()
        
        if not topic:
            return False
            
        logger.info(f"🏷️ Locked Topic {topic.id} for Category Correction: '{topic.title}'")
        
        # Create Job record
        job_id = await create_job_record(session, "CATEGORY_AGENT", payload={"topic_id": topic.id, "title": topic.title})
        await update_job_status(session, job_id, "RUNNING")
        
        # Commit job creation
        await session.commit()
        
        # 1. Get related articles for category context
        articles_query = (
            select(RawArticle)
            .join(TopicArticle, TopicArticle.article_id == RawArticle.id)
            .where(TopicArticle.topic_id == topic.id)
            .limit(5)
        )
        articles_res = await session.execute(articles_query)
        articles = articles_res.scalars().all()
        
        # Build context text
        context_text = "\n\n".join([f"Article: {a.title}\n{a.content[:500]}" for a in articles if a.content])
        
        # 2. Call AI to determine category
        ai_gen = AIContentGenerator(session)
        providers = await ai_gen._get_enabled_providers()
        if not providers:
            logger.error("No enabled AI providers found.")
            await update_job_status(session, job_id, "FAILED", error="No AI providers enabled")
            return False
            
        prompt = f"""You are a News Categorization Agent.
Analyze the following news topic and its related article snippets.
Topic Title: {topic.title}

Context:
{context_text}

Your task is to select the single most accurate category for this topic.
Choose ONLY from these standard categories: {", ".join(sorted(VALID_CATEGORIES))}

Respond with ONLY the category name in lowercase. No explanation, no punctuation.
"""

        try:
            provider = providers[0]
            suggested_category = await ai_gen._call_ai_provider(provider, prompt, max_tokens=20)
            suggested_category = suggested_category.strip().lower()
            
            # Basic validation
            if suggested_category not in VALID_CATEGORIES:
                logger.warning(f"AI suggested non-standard category: {suggested_category}")
            
            # Update Topic
            old_category = topic.category
            topic.category = suggested_category
            topic.analysis_status = 'categorized'
            
            logger.info(f"✅ Topic {topic.id} categorized: '{old_category}' -> '{suggested_category}'")
            await update_job_status(session, job_id, "SUCCESS", result={"topic_id": topic.id, "old_category": old_category, "new_category": suggested_category})
            
        except Exception as ai_err:
            logger.error(f"AI Error during categorization: {ai_err}")
            await update_job_status(session, job_id, "FAILED", error=str(ai_err))
            topic.analysis_status = 'failed'
        
        session.add(topic)
        await session.commit()
            
        return True
        
    except Exception as e:
        logger.error(f"Error in category correction agent: {e}")
        try:
            if 'job_id' in locals():
                await update_job_status(session, job_id, "FAILED", error=str(e))
        except:
            pass
        return False

async def worker_loop():
    """Continuously poll the database for verified topics."""
    logger.info("🏷️ Starting Category Correction Agent worker loop...")
    
    while True:
        try:
            async with AsyncSessionLocal() as session:
                processed_something = await process_category_correction(session)
                
            if not processed_something:
                await asyncio.sleep(10) # Less frequent than others as it's the final stage
            else:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Critical error in category worker loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Category Correction Agent shutting down.")
