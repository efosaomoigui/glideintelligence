from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Topic, TopicArticle, RawArticle, ArticleEmbedding
from pgvector.sqlalchemy import Vector
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class ClusteringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_or_create_topic(self, embedding: List[float], article_title: str, threshold: float = 0.8) -> int:
        """
        Find an existing topic with high similarity or create a new one.
        threshold: Cosine similarity threshold (0 to 1).
        """
        # Search for similar articles using pgvector
        # Cosine distance = 1 - cosine similarity. So threshold 0.8 means distance < 0.2
        distance_threshold = 1 - threshold
        
        query = (
            select(ArticleEmbedding.article_id, ArticleEmbedding.embedding.cosine_distance(embedding).label("distance"))
            .order_by("distance")
            .limit(1)
        )
        
        result = await self.db.execute(query)
        match = result.first()
        
        if match and match.distance < distance_threshold:
            # Found similar article, get its topic
            topic_query = select(TopicArticle.topic_id).where(TopicArticle.article_id == match.article_id)
            topic_res = await self.db.execute(topic_query)
            topic_id = topic_res.scalar()
            if topic_id:
                return topic_id

        # No close match, create new topic
        
        # Enhanced: Generate a better title using AI if possible
        final_title = article_title
        import os
        if not os.getenv("GLIDE_SKIP_AI_TITLES"):
            try:
                from app.services.ai.local_inference import local_inference
                # Generate a title (shorter version of original)
                # Increased max_length from 15 to 40 to prevent truncation
                summary = local_inference.generate_summary(article_title, max_length=40, min_length=10)
                
                # Only use summary if it's a valid length and not just a cut-off
                if summary and 10 < len(summary) < len(article_title) + 10:
                    final_title = summary
                else:
                    final_title = article_title
            except Exception as e:
                logger.warning(f"AI title generation failed: {e}. Falling back to article title.")
                final_title = article_title

        # Check for exact title match BEFORE creating
        # This prevents UniqueViolationError if another article with identical title exists
        # but wasn't found via embedding similarity (e.g. if embeddings are far apart or using hash fallback)
        existing_title_query = select(Topic).where(Topic.title == final_title)
        existing_title_res = await self.db.execute(existing_title_query)
        existing_topic = existing_title_res.scalar_one_or_none()
        if existing_topic:
            return existing_topic.id

        from app.utils.text import slugify
        import uuid
        
        # Generate generic slug
        base_slug = slugify(final_title)
        # Ensure uniqueness by appending short random string
        unique_suffix = str(uuid.uuid4())[:8]
        slug = f"{base_slug}-{unique_suffix}"

        new_topic = Topic(
            title=final_title,
            description="",  # AI Analysis will populate this with a proper summary
            is_trending=False,
            slug=slug,
            status="developing",
            importance_score=0.1,
            view_count=0,
            confidence_score=0.5,
            source_count=1,
            coverage_level="low"
        )
        self.db.add(new_topic)
        await self.db.commit()
        await self.db.refresh(new_topic)
        return new_topic.id

    async def assign_article_to_topic(self, article_id: int, topic_id: int):
        """Link an article to a topic and update its metadata."""
        assoc = TopicArticle(article_id=article_id, topic_id=topic_id)
        self.db.add(assoc)
        await self.db.commit()
        
        # Update metadata
        await self.refresh_topic_metadata(topic_id)

    async def refresh_topic_metadata(self, topic_id: int):
        """Calculate and update source count, confidence, and coverage level."""
        from datetime import datetime
        
        # 1. Get all articles in this topic
        query = (
            select(RawArticle.source_id, func.count(RawArticle.id))
            .join(TopicArticle, TopicArticle.article_id == RawArticle.id)
            .where(TopicArticle.topic_id == topic_id)
            .group_by(RawArticle.source_id)
        )
        result = await self.db.execute(query)
        sources_data = result.all()
        
        source_count = len(sources_data)
        article_count = sum(d[1] for d in sources_data)
        
        # 2. Logic for coverage level
        coverage = "low"
        if source_count >= 5:
            coverage = "high"
        elif source_count >= 3:
            coverage = "medium"
            
        # 3. Simple confidence score logic (normalized by source diversity)
        confidence = min(1.0, (source_count * 0.2) + (article_count * 0.05))
        
        # 4. Update topic
        topic_query = select(Topic).where(Topic.id == topic_id)
        topic_res = await self.db.execute(topic_query)
        topic = topic_res.scalar_one()
        
        topic.source_count = source_count
        topic.coverage_level = coverage
        topic.confidence_score = confidence
        topic.last_verified_at = datetime.now()
        
        # Simple Trending Logic: If covered by multiple sources or has significant volume
        topic.is_trending = (source_count >= 2 or article_count >= 3)
        
        await self.db.commit()
