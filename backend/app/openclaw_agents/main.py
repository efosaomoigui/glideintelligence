import asyncio
import logging
import os
import sys

# Configure logging to stdout so Docker can capture it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("openclaw_agents")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Import the centralized database dependencies
from app.database import AsyncSessionLocal
from app.models.topic import Topic, TopicArticle, TopicAnalysis, TopicSentimentBreakdown
from app.models.article import RawArticle
from app.models.intelligence import SourcePerspective, IntelligenceCard
from app.models.impact import RegionalImpact, ImpactCategory
from app.models.interaction import Poll, PollOption
from app.constants import VALID_CATEGORIES
import json
from app.services.ai.content_generator import AIContentGenerator, safe_encode
from app.utils.jobs import create_job_record, update_job_status

async def process_next_topic(session: AsyncSession) -> bool:
    """
    Fetches the next available topic for intelligence enrichment.
    Uses FOR UPDATE SKIP LOCKED to ensure safe concurrent processing.
    Returns True if a topic was processed, False otherwise.
    """
    try:
        logger.info("Checking for pending topics...")
        
        # 1. Lock and Update Topic
        query = (
            select(Topic)
            .where(Topic.analysis_status.in_(['pending', 'pipeline_failed']))
            .order_by(Topic.updated_at.desc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        
        result = await session.execute(query)
        topic = result.scalar_one_or_none()
        
        if not topic:
            logger.info("No pending topics found (or all currently locked).")
            return False
            
        logger.info(f"🔒 Locked topic for enrichment ({topic.analysis_status}): {topic.id} - '{topic.title}'")
        
        # Keep track of what we need to do
        is_recovery = topic.analysis_status == 'pipeline_failed'
        
        # Transition Topic to processing
        topic.analysis_status = 'processing'
        session.add(topic)
        
        # Create a Job record for the Admin UI
        job_id = await create_job_record(session, "INTELLIGENCE_AGENT", payload={"topic_id": topic.id, "title": topic.title})
        await update_job_status(session, job_id, "RUNNING")
        
        # Commit the status change and job creation so others see it's taken
        await session.commit()
        
        # 2. Feed topic data to OpenClaw agent
        # Re-fetch articles (we need a new transaction or just use session)
        articles_query = (
            select(RawArticle)
            .join(TopicArticle, TopicArticle.article_id == RawArticle.id)
            .where(TopicArticle.topic_id == topic.id)
            .limit(10)
        )
        articles_res = await session.execute(articles_query)
        articles = articles_res.scalars().all()
        
        # Build combined text from articles
        articles_text = "\n\n".join([f"Source {i+1}: {a.title}\n{a.content[:1000]}" for i, a in enumerate(articles) if a.content])
        
        # Ensure we have content
        if not articles_text:
            topic.analysis_status = 'complete' 
            await update_job_status(session, job_id, "SUCCESS", result={"status": "no_content"})
            await session.commit()
            return True

        logger.info(f"Synthesizing {len(articles)} articles for topic {topic.id}...")
        
        # Setup AI Generator
        ai_gen = AIContentGenerator(session)
        providers = await ai_gen._get_enabled_providers()
        if not providers:
            logger.error("No enabled AI providers found for intelligence agent.")
            await update_job_status(session, job_id, "FAILED", error="No AI providers enabled")
            return False
            
        recovery_instruction = ""
        if is_recovery:
            recovery_instruction = """
This topic failed the primary pipeline. Provide a FULL INTELLIGENCE report including sentiment, impacts, and perspectives.
Additional requirements for your JSON response:
- "sentiment_breakdown": [{"dimension_type": "...", "dimension_value": "...", "sentiment": "pos/neg/neu", "sentiment_score": 0.5, "percentage": 100, "icon": "emoji", "description": "..."}]
- "source_perspectives": [{"source_name": "...", "source_type": "...", "frame_label": "...", "sentiment": "...", "sentiment_percentage": "...", "key_narrative": "..."}]
- "regional_impacts": [{"impact_category": "...", "icon": "...", "title": "...", "value": "...", "severity": "low/mid/high", "context": "..."}]
- "intelligence_card": {"category": "...", "icon": "...", "title": "...", "description": "...", "trend_percentage": "...", "is_positive": true}
"""

        prompt = f"""You are an OpenClaw Intelligence Agent. 
Generate a highly structured intelligence report for the following topic:
Title: {topic.title}
Current Category: {topic.category}
{recovery_instruction}

Source Content (Synthesize these documents, DO NOT just copy headlines):
{articles_text[:6000]}

Respond ONLY with a valid JSON object matching this exact structure:
{{
  "executive_summary": "A 2-3 sentence high-level summary of the entire situation.",
  "what_you_need_to_know": ["bullet 1", "bullet 2", "bullet 3"],
  "key_takeaways": ["takeaway 1", "takeaway 2"],
  "drivers_of_story": ["driver 1", "driver 2"],
  "strategic_implications": ["implication 1", "implication 2"],
  "regional_impact": ["impact 1", "impact 2"],
  "sentiment_summary": "A concise summary of the overall sentiment and public/media reaction.",
  "framing_overview": "How different media outlets or stakeholders are framing this story.",
  "suggested_category": "one of: {', '.join(sorted(VALID_CATEGORIES))}",
  "confidence_score": 0.85
  {', "sentiment_breakdown": [], "source_perspectives": [], "regional_impacts": [], "intelligence_card": {}' if is_recovery else ''}
}}"""

        try:
            provider = providers[0] # Use top priority provider
            response_text = await ai_gen._call_ai_provider(provider, prompt, max_tokens=2000, timeout_seconds=90)
            json_text = ai_gen._extract_json(response_text)
            report_data = json.loads(json_text)
        except Exception as e:
            logger.error(f"Intelligence generation failed for topic {topic.id}: {e}")
            topic.analysis_status = 'failed'
            # Update topic and job in a new transaction
            await update_job_status(session, job_id, "FAILED", error=str(e))
            session.add(topic)
            await session.commit()
            return True
            
        # 3. Receive enriched data & Update topic analysis metadata
        analysis_query = select(TopicAnalysis).where(TopicAnalysis.topic_id == topic.id)
        analysis_res = await session.execute(analysis_query)
        analysis = analysis_res.scalar_one_or_none()
        
        if not analysis:
            analysis = TopicAnalysis(topic_id=topic.id, summary="")
            session.add(analysis)
            
        analysis.executive_summary = report_data.get('executive_summary', '')
        analysis.what_you_need_to_know = report_data.get('what_you_need_to_know', [])
        analysis.key_takeaways = report_data.get('key_takeaways', [])
        analysis.drivers_of_story = report_data.get('drivers_of_story', [])
        analysis.strategic_implications = report_data.get('strategic_implications', [])
        analysis.regional_impact = report_data.get('regional_impact', [])
        analysis.sentiment_summary = report_data.get('sentiment_summary', '')
        analysis.framing_overview = report_data.get('framing_overview', '')
        
        # SYNC: If basic summary is missing, use executive summary
        if not (analysis.summary or "").strip():
            logger.info(f"Syncing missing summary with executive_summary for topic {topic.id}")
            analysis.summary = analysis.executive_summary
        
        # Update category if suggested and it matches our VALID_CATEGORIES (single source of truth)
        suggested_cat = report_data.get('suggested_category', '').lower().strip()
        if suggested_cat and suggested_cat in VALID_CATEGORIES:
            if not topic.category or topic.category == 'general' or topic.category != suggested_cat:
                logger.info(f"Updating category for topic {topic.id} from {topic.category} to {suggested_cat}")
                topic.category = suggested_cat
        else:
            if suggested_cat:
                logger.warning(f"AI suggested invalid category '{suggested_cat}' for topic {topic.id}. Valid: {VALID_CATEGORIES}")
        
        try:
            conf = float(report_data.get('confidence_score', 0.8))
            analysis.confidence_score = conf
        except ValueError:
            pass
        
        # If recovery, store the extra tables
        if is_recovery:
            from sqlalchemy import delete
            # Sentiment
            if report_data.get('sentiment_breakdown'):
                await session.execute(delete(TopicSentimentBreakdown).where(TopicSentimentBreakdown.topic_id == topic.id))
                for item in report_data['sentiment_breakdown']:
                    session.add(TopicSentimentBreakdown(
                        topic_id=topic.id,
                        dimension_type=safe_encode(item.get("dimension_type", "General")),
                        dimension_value=safe_encode(item.get("dimension_value", "All")),
                        sentiment=safe_encode(item.get("sentiment", "neutral")),
                        sentiment_score=item.get("sentiment_score", 0.0),
                        percentage=item.get("percentage", 100),
                        icon=safe_encode(item.get("icon", "📊")),
                        description=safe_encode(item.get("description", ""))
                    ))
            
            # Perspectives
            if report_data.get('source_perspectives'):
                await session.execute(delete(SourcePerspective).where(SourcePerspective.topic_id == topic.id))
                for persp in report_data['source_perspectives']:
                    session.add(SourcePerspective(
                        topic_id=topic.id,
                        source_name=safe_encode(persp.get("source_name", "Unknown")),
                        source_type=persp.get("source_type", "website"),
                        frame_label=safe_encode(persp.get("frame_label", "Neutral")),
                        sentiment=safe_encode(persp.get("sentiment", "neutral")),
                        sentiment_percentage=safe_encode(persp.get("sentiment_percentage", "0%")),
                        key_narrative=safe_encode(persp.get("key_narrative", ""))
                    ))

            # Regional Impact
            if report_data.get('regional_impacts'):
                await session.execute(delete(RegionalImpact).where(RegionalImpact.topic_id == topic.id))
                for impact_data in report_data['regional_impacts']:
                    cat_key = safe_encode(impact_data.get("impact_category", "general"))
                    regional_impact = RegionalImpact(
                        topic_id=topic.id,
                        impact_category=cat_key,
                        icon=safe_encode(impact_data.get("icon", "📝")),
                        title=safe_encode(impact_data.get("title", "Impact")),
                        value=safe_encode(impact_data.get("value", "Identified")),
                        severity=safe_encode(impact_data.get("severity", "medium")),
                        context=safe_encode(impact_data.get("context", "")),
                        is_current=True
                    )
                    session.add(regional_impact)
            
            # Intelligence Card
            if report_data.get('intelligence_card'):
                await session.execute(delete(IntelligenceCard).where(IntelligenceCard.topic_id == topic.id))
                card_data = report_data['intelligence_card']
                session.add(IntelligenceCard(
                    topic_id=topic.id,
                    category=safe_encode(card_data.get("category", topic.category)),
                    icon=safe_encode(card_data.get("icon", "📊")),
                    title=safe_encode(card_data.get("title", topic.title[:60])),
                    description=safe_encode(card_data.get("description", "")),
                    trend_percentage=safe_encode(card_data.get("trend_percentage", "0%")),
                    is_positive=card_data.get("is_positive", True)
                ))

        logger.info(f"✅ Successfully generated and saved Intelligence Report for topic {topic.id} (recovery={is_recovery})")
        
        # Generate contextual poll for this topic
        await _generate_contextual_poll(session, topic, ai_gen, providers)
        
        # Ensure topic status is stable
        if topic.status != 'stable':
            topic.status = 'stable'
        
        # Update topic analysis_status to 'complete'
        topic.analysis_status = 'complete'
        
        # Update Job Record
        await update_job_status(session, job_id, "SUCCESS", result={"topic_id": topic.id, "status": "complete"})
        
        # Final commit
        await session.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing topic: {e}")
        # If we failed but have a job_id, update it
        try:
            # We need job_id to be visible in this scope if it was created
            if 'job_id' in locals():
                await update_job_status(session, job_id, "FAILED", error=str(e))
        except:
            pass
        return False

async def _generate_contextual_poll(session, topic, ai_gen, providers):
    """Generate a single contextual poll for a topic and save it to the database."""
    try:
        from sqlalchemy import select as sa_select
        # Skip if a poll already exists for this topic
        existing = await session.execute(sa_select(Poll).where(Poll.topic_id == topic.id))
        if existing.scalar_one_or_none():
            logger.info(f"Poll already exists for topic {topic.id}, skipping generation.")
            return

        poll_prompt = f"""You are an intelligence analyst creating a reader engagement poll for a news topic.

Topic: {topic.title}

Generate a single, thought-provoking poll question about this topic that invites readers to share their opinion on a key aspect of the story. Respond ONLY with a valid JSON object:
{{
  "question": "Your poll question here?",
  "options": ["Option A", "Option B", "Option C", "Option D"]
}}

Rules:
- Question must be directly relevant to the topic.
- Between 3 and 4 options. No "Other" option.
- Options should represent genuinely different perspectives or outcomes.
"""
        provider = providers[0]
        response_text = await ai_gen._call_ai_provider(provider, poll_prompt, max_tokens=400, timeout_seconds=30)
        json_text = ai_gen._extract_json(response_text)
        poll_data = json.loads(json_text)

        question = poll_data.get("question", "").strip()
        options = poll_data.get("options", [])

        if not question or len(options) < 2:
            logger.warning(f"Poll generation returned invalid data for topic {topic.id}")
            return

        # Save Poll
        from datetime import timedelta
        poll = Poll(
            topic_id=topic.id,
            question=safe_encode(question),
            poll_type="single_choice",
            is_active=True,
            closes_at=None,  # Open-ended for now
            created_by_id=None  # System-generated
        )
        session.add(poll)
        await session.flush()  # Get poll.id

        for i, opt_text in enumerate(options[:4]):
            session.add(PollOption(
                poll_id=poll.id,
                option_text=safe_encode(opt_text.strip()),
                display_order=i
            ))

        logger.info(f"✅ Contextual poll created for topic {topic.id}: '{question}'")

    except Exception as poll_err:
        logger.warning(f"Could not generate poll for topic {topic.id} (non-critical): {poll_err}")
        # Don't re-raise — poll generation failure must not break the main enrichment


async def worker_loop():
    """Continuously poll the database for new topics."""
    logger.info("🚀 Starting OpenClaw Agent Service worker loop...")
    
    while True:
        try:
            # Get a fresh DB session from the pool
            async with AsyncSessionLocal() as session:
                processed_something = await process_next_topic(session)
                
            # If we found nothing, back off slightly to reduce DB polling spam
            if not processed_something:
                await asyncio.sleep(5)
            else:
                # Give a tiny breather after processing before grabbing the next
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Critical error in worker loop: {e}")
            await asyncio.sleep(5)  # Backoff on error

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down OpenClaw Agent Service.")
