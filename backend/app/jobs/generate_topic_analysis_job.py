from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models import (
    Topic, TopicAnalysis, TopicSentimentBreakdown, TopicArticle, 
    RawArticle, AISummary
)
from app.models.interaction import Poll, PollOption, PollVote
from app.models.intelligence import CategoryConfig, SourcePerspective, IntelligenceCard
from app.models.impact import RegionalImpact, ImpactCategory
from app.services.ai.summarization_service import SummarizationService
from app.services.ai.content_generator import AIContentGenerator, RateLimiter, CostTracker, safe_encode
from app.constants import VALID_CATEGORIES, DEFAULT_CATEGORY
from datetime import datetime
import logging
import os
import asyncio
from typing import Dict, List
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class GenerateTopicAnalysisJob:
    """
    🚀 ENHANCED: Background job with smart features.
    
    New Features:
    - Streaming storage (saves each component immediately)
    - Better error handling
    - Encoding fixes throughout
    - Progress tracking
    """
    
    def __init__(self, db: AsyncSession, rate_limiter: RateLimiter = None, cost_tracker: CostTracker = None):
        self.db = db
        self.ai_svc = SummarizationService(db)
        self.content_gen = AIContentGenerator(db, rate_limiter, cost_tracker)
        self.use_optimized = os.getenv('USE_OPTIMIZED_PIPELINE', 'true').lower() == 'true'
        self.daily_budget = float(os.getenv('DAILY_BUDGET_USD', '5.0'))

    async def execute(self, topic_id: int):
        """Execute analysis with enhanced features."""
        
        logger.info(f"Starting analysis for topic {topic_id} (optimized={self.use_optimized})...")
        
        # Link AI usage logs to this topic
        self.content_gen._current_topic_id = topic_id
        
        try:
            # Step 1: Fetch topic
            t_query = select(Topic).where(Topic.id == topic_id)
            t_res = await self.db.execute(t_query)
            topic = t_res.scalar_one_or_none()
            
            if not topic:
                logger.warning(f"Topic {topic_id} not found")
                return
            
            # Fix encoding in topic data
            topic.title = safe_encode(topic.title)
            if topic.description:
                topic.description = safe_encode(topic.description)

            # Step 2: Fetch articles with source
            query = (
                select(RawArticle)
                .join(TopicArticle)
                .options(selectinload(RawArticle.source))
                .where(TopicArticle.topic_id == topic_id)
            )
            result = await self.db.execute(query)
            articles = result.scalars().all()
            
            if not articles:
                logger.warning(f"No articles for topic {topic_id}")
                return
            
            # Fix encoding in articles
            for article in articles:
                if article.title:
                    article.title = safe_encode(article.title)
                if article.content:
                    article.content = safe_encode(article.content)
            
            contents = [a.content for a in articles if a.content]
            if not contents:
                logger.warning(f"No content in articles for topic {topic_id}")
                return
                 
            combined_text = "\n\n".join(contents[:5])

            # Step 3: Fetch category config — direct lookup using canonical category name
            category_config = None
            raw_category = (topic.category or "").strip().lower()

            # Only look up if it's a known canonical category
            if raw_category in VALID_CATEGORIES:
                config_query = select(CategoryConfig).where(CategoryConfig.category == raw_category)
                config_res = await self.db.execute(config_query)
                category_config = config_res.scalar_one_or_none()

            if not category_config:
                # Try the 'general' catch-all (always exists after seeding)
                logger.warning(
                    f"No config for category '{topic.category}' on topic {topic_id} "
                    f"— falling back to '{DEFAULT_CATEGORY}'"
                )
                fallback_query = select(CategoryConfig).where(CategoryConfig.category == DEFAULT_CATEGORY)
                fallback_res = await self.db.execute(fallback_query)
                category_config = fallback_res.scalar_one_or_none()

            if not category_config:
                logger.error(
                    f"'{DEFAULT_CATEGORY}' config missing for topic {topic_id}. "
                    f"Run: python seed_category_configs.py"
                )
                topic.status = "stable"
                topic.overall_sentiment = "neutral"
                await self.db.commit()
                return

            # Step 4: Generate basic summary
            analysis_data = await self.ai_svc.generate_summary_pipeline(contents)
            
            # Fix encoding in summary
            if 'summary' in analysis_data:
                analysis_data['summary'] = safe_encode(analysis_data['summary'])
            
            # 🚀 STREAMING STORAGE: Save summary immediately
            await self._store_basic_summary(topic_id, analysis_data)
            await self.db.commit()
            logger.info(f"✅ Basic summary saved (streaming)")

            overall_sentiment = "neutral"
            sentiment_score = 0.0

            # Step 5-8: Enhanced Analysis
            if category_config:
                if self.use_optimized:
                    await self._execute_optimized_analysis(
                        topic, topic_id, combined_text, articles, category_config, analysis_data.get('summary', '')
                    )
                else:
                    logger.warning("Legacy mode not implemented in enhanced version")
                    raise NotImplementedError("Use optimized mode (USE_OPTIMIZED_PIPELINE=true)")
                
                # Calculate overall sentiment
                sentiment_query = select(TopicSentimentBreakdown).where(TopicSentimentBreakdown.topic_id == topic_id)
                sentiment_res = await self.db.execute(sentiment_query)
                sentiment_items = sentiment_res.scalars().all()
                
                if sentiment_items:
                    avg_score = sum(s.sentiment_score for s in sentiment_items) / len(sentiment_items)
                    sentiment_score = avg_score
                    if avg_score > 0.2:
                        overall_sentiment = "positive"
                    elif avg_score < -0.2:
                        overall_sentiment = "negative"

            # Step 9: Update topic
            topic.overall_sentiment = overall_sentiment
            topic.sentiment_score = sentiment_score
            topic.status = "stable"
            topic.last_verified_at = datetime.now()
            
            # Sync summary to topic description for frontend fallback
            if 'summary' in analysis_data:
                topic.description = analysis_data['summary']
            
            # Step 10: Final commit
            await self.db.commit()
            logger.info(f"✅ Analysis completed for topic {topic_id}")

        except Exception as e:
            error_msg = safe_encode(str(e))
            logger.error(f"❌ Error in analysis for topic {topic_id}: {error_msg}")
            await self.db.rollback()
            
            # Mark as failed
            try:
                t_res = await self.db.execute(select(Topic).where(Topic.id == topic_id))
                topic_ref = t_res.scalar_one_or_none()
                if topic_ref:
                    topic_ref.status = 'analysis_failed'
                    topic_ref.overall_sentiment = 'error'
                    if not topic_ref.metadata_:
                        topic_ref.metadata_ = {}
                    topic_ref.metadata_['last_error'] = error_msg[:200]
                    topic_ref.metadata_['error_at'] = str(datetime.now())
                    await self.db.commit()
                    logger.info(f"Marked topic {topic_id} as 'analysis_failed'")
            except Exception as e2:
                logger.error(f"Failed to set error state: {e2}")
            
            raise e
    
    async def _store_basic_summary(self, topic_id: int, analysis_data: Dict):
        """Store basic summary (Step 4) - called immediately."""
        
        # Store in topic_analysis
        existing = await self.db.execute(
            select(TopicAnalysis).where(TopicAnalysis.topic_id == topic_id)
        )
        analysis = existing.scalar_one_or_none()
        
        if analysis:
            analysis.summary = analysis_data["summary"]
            analysis.facts = analysis_data.get("facts", [])
            analysis.regional_framing = analysis_data.get("regional_framing", {})
        else:
            analysis = TopicAnalysis(
                topic_id=topic_id,
                summary=analysis_data["summary"],
                facts=analysis_data.get("facts", []),
                regional_framing=analysis_data.get("regional_framing", {})
            )
            self.db.add(analysis)
        
        # Store in ai_summaries
        ai_summary = AISummary(
            topic_id=topic_id,
            summary_type="60_second",
            content=analysis_data["summary"],
            bullet_points=analysis_data.get("facts", []),
            model_used=analysis_data.get("provider", "Unknown"),
            quality_score=analysis_data.get("confidence_score", 0.0),
            is_current=True,
            generated_at=datetime.now()
        )
        self.db.add(ai_summary)
    
    async def _execute_optimized_analysis(
        self,
        topic: Topic,
        topic_id: int,
        combined_text: str,
        articles: list,
        category_config: CategoryConfig,
        topic_summary: str = ""
    ):
        """🚀 ENHANCED: Multi-stage API call with streaming storage."""
        
        # Prepare sources
        sources_data = [
            {
                "name": safe_encode(a.source.name if a.source else "Unknown"),
                "headline": safe_encode(a.title),
                "type": a.source.type if a.source else "unknown"
            }
            for a in articles if a.source
        ]
        
        # Make unified call
        analysis_result = await self.content_gen.generate_complete_analysis(
            topic_title=topic.title,
            topic_content=combined_text,
            category_config=category_config,
            sources=sources_data,
            topic_summary=topic_summary,
            topic_id=topic_id,
            timeout_seconds=90,
            daily_budget=self.daily_budget
        )
        
        logger.info(f"✅ AI analysis received ({analysis_result['provider_used']}, {analysis_result['tokens_used']} tokens, ${analysis_result['cost_estimate']:.4f})")
        
        # 🚀 STREAMING STORAGE: Save each component immediately with commits
        
        # Component 1: Sentiment breakdown
        await self._store_sentiment_breakdown(topic_id, analysis_result['sentiment_breakdown'])
        await self.db.commit()
        logger.info(f"✅ Sentiment breakdown saved ({len(analysis_result['sentiment_breakdown'])} items)")
        
        # Component 2: Source perspectives
        await self._store_source_perspectives(topic_id, analysis_result['source_perspectives'])
        await self.db.commit()
        logger.info(f"✅ Source perspectives saved ({len(analysis_result['source_perspectives'])} items)")
        
        # Component 3: Regional impacts
        await self._store_regional_impacts(topic_id, analysis_result['regional_impacts'])
        await self.db.commit()
        logger.info(f"✅ Regional impacts saved ({len(analysis_result['regional_impacts'])} items)")
        
        # Component 4: Intelligence card
        await self._store_intelligence_card(topic_id, topic.category, analysis_result['intelligence_card'])
        await self.db.commit()
        logger.info(f"✅ Intelligence card saved")

        # Component 5: Contextual Poll
        if 'poll' in analysis_result:
            await self._store_poll(topic_id, analysis_result['poll'])
            await self.db.commit()
            logger.info(f"✅ Contextual poll saved")

        # Component 6: Category Verification
        if 'verified_category' in analysis_result:
            v_cat = analysis_result['verified_category'].lower().strip()
            if v_cat in VALID_CATEGORIES and v_cat != (topic.category or "").lower():
                logger.info(f"🔄 Updating topic {topic_id} category: {topic.category} -> {v_cat}")
                topic.category = v_cat

        # Component 7: Enhanced Metadata
        if 'key_takeaways' in analysis_result or 'core_drivers' in analysis_result:
            metadata = topic.metadata_ or {}
            metadata_copy = dict(metadata) # copy to ensure SQLAlchemy detects change
            if 'key_takeaways' in analysis_result:
                metadata_copy['key_takeaways'] = safe_encode(analysis_result['key_takeaways'])
            if 'core_drivers' in analysis_result:
                metadata_copy['core_drivers'] = [safe_encode(d) for d in analysis_result['core_drivers']]
            topic.metadata_ = metadata_copy

        await self.db.commit()
    
    async def _store_sentiment_breakdown(self, topic_id: int, items: List[Dict]):
        """Store sentiment breakdown with encoding fixes."""
        await self.db.execute(delete(TopicSentimentBreakdown).where(TopicSentimentBreakdown.topic_id == topic_id))
        
        for item in items:
            sentiment = TopicSentimentBreakdown(
                topic_id=topic_id,
                dimension_type=safe_encode(item.get("dimension_type", "general")),
                dimension_value=safe_encode(item.get("dimension_value", "topic")),
                sentiment=safe_encode(item.get("sentiment", "neutral")),
                sentiment_score=item.get("sentiment_score", 0.0),
                percentage=item.get("percentage", 0),
                icon=safe_encode(item.get("icon", "📊")),
                description=safe_encode(item.get("description", ""))
            )
            self.db.add(sentiment)
    
    async def _store_source_perspectives(self, topic_id: int, items: List[Dict]):
        """Store source perspectives with encoding fixes."""
        await self.db.execute(delete(SourcePerspective).where(SourcePerspective.topic_id == topic_id))
        
        for persp in items:
            perspective = SourcePerspective(
                topic_id=topic_id,
                source_name=safe_encode(persp["source_name"]),
                source_type=persp.get("source_type"),
                frame_label=safe_encode(persp["frame_label"]),
                sentiment=safe_encode(persp["sentiment"]),
                sentiment_percentage=safe_encode(persp["sentiment_percentage"]),
                key_narrative=safe_encode(persp["key_narrative"])
            )
            self.db.add(perspective)
    
    async def _store_regional_impacts(self, topic_id: int, items: List[Dict]):
        """Store regional impacts with encoding fixes."""
        await self.db.execute(delete(RegionalImpact).where(RegionalImpact.topic_id == topic_id))
        
        for impact_data in items:
            cat_key = safe_encode(impact_data.get("impact_category", "general"))
            
            # Ensure ImpactCategory exists
            cat_query = select(ImpactCategory).where(ImpactCategory.slug == cat_key)
            cat_result = await self.db.execute(cat_query)
            impact_category_obj = cat_result.scalar_one_or_none()
            
            name_val = safe_encode(cat_key.replace("_", " ").title())
            if not impact_category_obj:
                impact_category_obj = ImpactCategory(
                    name=name_val,
                    slug=cat_key,
                    icon=safe_encode(impact_data.get("icon", "📊")),
                    display_order=0
                )
                try:
                    async with self.db.begin_nested():
                        self.db.add(impact_category_obj)
                        await self.db.flush()
                except IntegrityError:
                    # Created by another concurrent task, fetch it
                    await self.db.rollback() # Rollback the nested transaction
                    cat_result = await self.db.execute(select(ImpactCategory).where(ImpactCategory.name == name_val))
                    impact_category_obj = cat_result.scalar_one_or_none()
            
            regional_impact = RegionalImpact(
                topic_id=topic_id,
                impact_category_id=impact_category_obj.id,
                impact_category=cat_key,
                icon=safe_encode(impact_data.get("icon", "📊")),
                title=safe_encode(impact_data.get("title", cat_key.replace("_", " ").title())),
                value=safe_encode(impact_data.get("value", "Impact identified")),
                severity=safe_encode(impact_data.get("severity", "medium")),
                context=safe_encode(impact_data.get("context", "")),
                is_current=True
            )
            self.db.add(regional_impact)
    
    async def _store_intelligence_card(self, topic_id: int, category: str, card_data: Dict):
        """Store intelligence card with encoding fixes."""
        await self.db.execute(delete(IntelligenceCard).where(IntelligenceCard.topic_id == topic_id))
        
        card = IntelligenceCard(
            topic_id=topic_id,
            category=safe_encode(card_data.get("category", category)),
            icon=safe_encode(card_data.get("icon", "")),
            title=safe_encode(card_data.get("title", "")),
            description=safe_encode(card_data.get("description", "")),
            trend_percentage=safe_encode(card_data.get("trend_percentage", "")),
            is_positive=card_data.get("is_positive", True),
            display_order=0
        )
        self.db.add(card)

    async def _store_poll(self, topic_id: int, poll_data: Dict):
        """Store contextual poll generated by AI."""
        # 1. Clean existing polls and their engagement data for this topic
        # Using manual child deletion to bypass potential RESTRICT constraints on direct execute
        existing_polls_res = await self.db.execute(select(Poll.id).where(Poll.topic_id == topic_id))
        poll_ids = existing_polls_res.scalars().all()
        if poll_ids:
            await self.db.execute(delete(PollVote).where(PollVote.poll_id.in_(poll_ids)))
            await self.db.execute(delete(PollOption).where(PollOption.poll_id.in_(poll_ids)))
            await self.db.execute(delete(Poll).where(Poll.id.in_(poll_ids)))
            
        question = safe_encode(poll_data.get("question", "What is your stance on this issue?"))
        options = poll_data.get("options", [])
        
        poll = Poll(
            topic_id=topic_id,
            question=question,
            poll_type="single_choice",
            is_active=True
        )
        self.db.add(poll)
        await self.db.flush() # flush to get poll.id
        
        for idx, opt in enumerate(options):
            option = PollOption(
                poll_id=poll.id,
                option_text=safe_encode(str(opt)),
                display_order=idx
            )
            self.db.add(option)
