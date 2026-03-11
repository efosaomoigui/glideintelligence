from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.models import (
    Topic, TopicAnalysis, TopicSentimentBreakdown, TopicArticle, 
    RawArticle, AISummary
)
from app.models.intelligence import CategoryConfig, SourcePerspective, IntelligenceCard
from app.models.impact import RegionalImpact, ImpactCategory
from app.services.ai.summarization_service import SummarizationService
from app.services.ai.content_generator import AIContentGenerator, RateLimiter, CostTracker, safe_encode
from datetime import datetime
import logging
import os
import asyncio
from typing import Dict, List

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

            # Step 3: Fetch category config
            category_config = None
            if topic.category:
                config_query = select(CategoryConfig).where(CategoryConfig.category == topic.category.lower())
                config_res = await self.db.execute(config_query)
                category_config = config_res.scalar_one_or_none()
            
            if not category_config:
                logger.warning(f"No category config for '{topic.category}'. Attempting 'general' fallback.")
                config_query = select(CategoryConfig).where(CategoryConfig.category == "general")
                config_res = await self.db.execute(config_query)
                category_config = config_res.scalar_one_or_none()
            
            if not category_config:
                logger.error(f"Critical: No 'general' fallback config found. Failing analysis for topic {topic_id}")
                topic.status = 'analysis_failed'
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
                        topic, topic_id, combined_text, articles, category_config
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
            topic.analysis_status = "pending" # Hand off to OpenClaw for enrichment
            topic.last_verified_at = datetime.now()
            
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
                    topic_ref.analysis_status = 'pipeline_failed' # Hand off to OpenClaw for recovery
                    topic_ref.overall_sentiment = 'error'
                    if not topic_ref.metadata_:
                        topic_ref.metadata_ = {}
                    topic_ref.metadata_['last_error'] = error_msg[:200]
                    topic_ref.metadata_['error_at'] = str(datetime.now())
                    await self.db.commit()
                    logger.info(f"Marked topic {topic_id} as 'analysis_failed'")
            except Exception as e2:
                logger.error(f"Failed to set error state: {e2}")
            
            return
    
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
        category_config: CategoryConfig
    ):
        """🚀 ENHANCED: Single API call with streaming storage."""
        
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
        result = await self.content_gen.generate_complete_analysis(
            topic_title=topic.title,
            topic_content=combined_text,
            category_config=category_config,
            sources=sources_data,
            timeout_seconds=90,
            daily_budget=self.daily_budget
        )
        
        logger.info(f"✅ AI analysis received ({result['provider_used']}, {result['tokens_used']} tokens, ${result['cost_estimate']:.4f})")
        
        # 🚀 STREAMING STORAGE: Save each component immediately with commits
        
        # Component 1: Sentiment breakdown
        await self._store_sentiment_breakdown(topic_id, result['sentiment_breakdown'])
        await self.db.commit()
        logger.info(f"✅ Sentiment breakdown saved ({len(result['sentiment_breakdown'])} items)")
        
        # Component 2: Source perspectives
        await self._store_source_perspectives(topic_id, result['source_perspectives'])
        await self.db.commit()
        logger.info(f"✅ Source perspectives saved ({len(result['source_perspectives'])} items)")
        
        # Component 3: Regional impacts
        await self._store_regional_impacts(topic_id, result['regional_impacts'])
        await self.db.commit()
        logger.info(f"✅ Regional impacts saved ({len(result['regional_impacts'])} items)")
        
        # Component 4: Intelligence card
        await self._store_intelligence_card(topic_id, topic.category, result['intelligence_card'])
        await self.db.commit()
        logger.info(f"✅ Intelligence card saved")

        # Component 5: Contextual Poll
        if result.get('poll'):
            await self._store_poll(topic_id, result['poll'])
            await self.db.commit()
            logger.info(f"✅ Contextual poll saved")

        # Handle Category Override
        if result.get('verified_category') and result['verified_category'].lower() != (topic.category or "").lower():
            old_cat = topic.category
            new_cat = result['verified_category']
            logger.info(f"🔄 Category override: {old_cat} -> {new_cat}")
            topic.category = new_cat
            await self.db.commit()
    
    async def _store_sentiment_breakdown(self, topic_id: int, items: List[Dict]):
        """Store sentiment breakdown with encoding fixes."""
        await self.db.execute(delete(TopicSentimentBreakdown).where(TopicSentimentBreakdown.topic_id == topic_id))
        
        for item in items:
            sentiment = TopicSentimentBreakdown(
                topic_id=topic_id,
                dimension_type=safe_encode(item["dimension_type"]),
                dimension_value=safe_encode(item["dimension_value"]),
                sentiment=safe_encode(item["sentiment"]),
                sentiment_score=item["sentiment_score"],
                percentage=item["percentage"],
                icon=safe_encode(item.get("icon", ""))[:50],
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
            
            if not impact_category_obj:
                impact_category_obj = ImpactCategory(
                    name=safe_encode(cat_key.replace("_", " ").title()),
                    slug=cat_key,
                    icon=safe_encode(impact_data.get("icon", "📊")),
                    display_order=0
                )
                self.db.add(impact_category_obj)
                await self.db.flush()
            
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
            icon=safe_encode(card_data.get("icon", ""))[:50],
            title=safe_encode(card_data.get("title", "")),
            description=safe_encode(card_data.get("description", "")),
            trend_percentage=safe_encode(card_data.get("trend_percentage", "")),
            is_positive=card_data.get("is_positive", True),
            display_order=0
        )
        self.db.add(card)

    async def _store_poll(self, topic_id: int, poll_data: Dict):
        """Store contextual poll and its options."""
        from app.models.interaction import Poll, PollOption
        
        # Deactivate old polls for this topic
        await self.db.execute(
            delete(Poll).where(Poll.topic_id == topic_id)
        )
        
        poll = Poll(
            topic_id=topic_id,
            question=safe_encode(poll_data["question"]),
            poll_type="single_choice",
            is_active=True,
            closes_at=None  # Or set a default like 7 days from now
        )
        self.db.add(poll)
        await self.db.flush()
        
        for i, opt_text in enumerate(poll_data.get("options", [])):
            option = PollOption(
                poll_id=poll.id,
                option_text=safe_encode(opt_text),
                display_order=i
            )
            self.db.add(option)
