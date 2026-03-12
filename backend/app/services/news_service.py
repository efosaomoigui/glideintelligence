from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import joinedload, selectinload, make_transient
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import math

from app.models import (
    Topic, RawArticle, TopicArticle, TopicAnalysis, 
    TopicSentimentBreakdown, TopicTrend, TopicVideo, Source, TopicRegionalCategory
)

class NewsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_home_data(self) -> dict:
        """Fetch data for the home page (trending topics and featured articles)."""
        

        # 1. Trending topics with loaded relations
        trending_topics_query = (
            select(Topic)
            .options(
                 selectinload(Topic.analysis),
                 selectinload(Topic.article_associations).joinedload(TopicArticle.article).joinedload(RawArticle.source)
            )
            .where(Topic.is_trending == True)
            .order_by(desc(Topic.updated_at))
            .limit(5)
        )
        trending_topics = (await self.db.execute(trending_topics_query)).unique().scalars().all()
        # Convert to list to allow appending
        trending_topics = list(trending_topics)
        
        # Fallback if not enough trending topics to fill the carousel (we want at least 3 for the UI)
        if len(trending_topics) < 5:
             existing_ids = [t.id for t in trending_topics]
             fallback_query = (
                select(Topic)
                .options(
                     selectinload(Topic.analysis),
                     selectinload(Topic.article_associations).joinedload(TopicArticle.article).joinedload(RawArticle.source)
                )
             )
             if existing_ids:
                 fallback_query = fallback_query.where(Topic.id.notin_(existing_ids))
                 
             fallback_query = fallback_query.order_by(desc(Topic.updated_at)).limit(5 - len(trending_topics))
             additional_topics = (await self.db.execute(fallback_query)).unique().scalars().all()
             trending_topics.extend(additional_topics)

        # Detach topics from session so _enrich can mutate attributes safely
        for t in trending_topics:
            self.db.expunge(t)
            make_transient(t)

        # Enrich topics for frontend
        enriched_topics = []
        for topic in trending_topics:
            enriched = self._enrich_topic_for_frontend(topic)
            enriched_topics.append(enriched)

        # 2. Featured articles (latest)
        latest_articles_query = (
            select(RawArticle, Source.name.label("source_name"))
            .join(Source)
            .order_by(desc(RawArticle.published_at))
            .limit(10)
        )
        latest_articles_result = await self.db.execute(latest_articles_query)
        latest_articles = []
        for row in latest_articles_result:
            article = row.RawArticle
            article.source_name = row.source_name
            latest_articles.append(article)
            
        # 3. Select Hero Article
        # Prefer an article from a trending topic if available, otherwise latest high-quality article
        hero_article = None
        if enriched_topics:
            # Pick the first article from the top trending topic
            top_topic = enriched_topics[0]
            if top_topic.articles:
                hero_article = top_topic.articles[0]
                # Enhance hero article with topic context
                hero_article.category = "Deep Dive" # or mapping
                hero_article.description = top_topic.description or hero_article.description
                hero_article.updated = top_topic.updated_at_str # Use topic's time string

                
                # New Hero Fields
                hero_article.source_count = top_topic.source_count
                hero_article.comment_count = top_topic.comment_count
                if top_topic.analysis:
                    hero_article.summary = top_topic.analysis.summary
                    hero_article.bullets = top_topic.analysis.facts or []
                else:
                    hero_article.summary = top_topic.description
                    hero_article.bullets = []
        
        if not hero_article and latest_articles:
             hero_article = latest_articles[0]
             hero_article.category = "Breaking News"
             # Use real description or summary if available
             hero_article.description = hero_article.description or hero_article.content[:200] + "..."
             
             # Calculate time ago for fallback hero
             hero_article.updated = "Recently"
             if hero_article.published_at:
                 diff = datetime.utcnow() - hero_article.published_at
                 seconds = diff.total_seconds()
                 if seconds < 3600:
                     hero_article.updated = f"{int(seconds // 60)} min ago"
                 elif seconds < 86400:
                     hero_article.updated = f"{int(seconds // 3600)} hours ago"
                 else:
                     hero_article.updated = f"{int(seconds // 86400)} days ago"

             # Fallback defaults
             hero_article.source_count = 1
             hero_article.comment_count = 0
             hero_article.summary = hero_article.description
             hero_article.bullets = []

        return {
            "trending_topics": enriched_topics,
            "latest_articles": latest_articles,
            "hero_article": hero_article,
            "pulse": self._get_pulse_data(enriched_topics)
        }

    async def get_hot_poll(self) -> Optional[dict]:
        """Fetch the most relevant active poll."""
        from app.models.interaction import Poll
        from app.schemas.interaction import PollSchema
        
        # Priority: Trending topic associates > Most voted > Recent
        query = (
            select(Poll)
            .options(selectinload(Poll.options))
            .where(Poll.is_active == True)
            .order_by(Poll.total_votes.desc(), Poll.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        poll = result.scalar_one_or_none()
        
        if poll:
            return PollSchema.model_validate(poll).model_dump()
        return None

    async def get_hot_comments(self, limit: int = 4) -> List[dict]:
        """Fetch highly engaged comments for 'Community Voices'."""
        from app.models.interaction import Comment
        from app.models.user import User
        
        query = (
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.moderation_status == "approved")
            .order_by((Comment.upvote_count + Comment.reply_count).desc(), Comment.created_at.desc())
            .limit(limit)
        )
        # If no approved comments, try pending or just any recent ones
        result = await self.db.execute(query)
        comments = result.scalars().all()
        
        if not comments:
             query = (
                select(Comment)
                .options(selectinload(Comment.user))
                .order_by(Comment.created_at.desc())
                .limit(limit)
            )
             result = await self.db.execute(query)
             comments = result.scalars().all()

        output = []
        import logging
        for c in comments:
            try:
                # Eager loaded user check
                user_obj = c.user if 'user' in c.__dict__ else None
                if not user_obj:
                    # Try to access normally as fallback (might trigger lazy-load if not detached)
                    try:
                        user_obj = c.user
                    except Exception:
                        continue
                
                if not user_obj:
                    continue
                    
                full_name = user_obj.full_name or user_obj.username
                role = user_obj.role.title() if user_obj.role else "Member"
                
                # Simple color generator
                colors = ["#c0392b", "#27ae60", "#2980b9", "#8e44ad", "#f39c12", "#2c3e50"]
                color = colors[len(full_name) % len(colors)]
                
                output.append({
                    "initials": "".join([n[0] for n in full_name.split() if n])[:2].upper(),
                    "name": full_name,
                    "role": role,
                    "quote": c.content,
                    "color": color
                })
            except Exception as e:
                logging.error(f"Error processing hot comment: {e}")
                continue
        
        return output

    def _get_pulse_data(self, topics) -> dict:
        """Generate dynamic pulse data from trending topics."""
        if not topics:
            return {
                "sentiment": {"label": "Neutral", "score": "+0%", "text": "Waiting for more data points...", "bar_width": "50%", "type": "neutral"},
                "context": {"label": "Analysis Pending", "name": "GlideIntelligence", "description": "System is aggregating initial data."},
                "regional": {"label": "West Africa", "name": "ECOWAS", "description": "Monitoring regional stability indicators."}
            }
            
        # 1. Aggregate Sentiment — sentiment_breakdown is a LIST of dimension rows
        total_score = 0.0
        scored_count = 0
        for t in topics:
            # Use topic-level overall_sentiment/sentiment_score if available
            if hasattr(t, 'sentiment_score') and t.sentiment_score is not None:
                total_score += t.sentiment_score
                scored_count += 1
            elif 'sentiment_breakdown' in t.__dict__ and t.sentiment_breakdown:
                # sentiment_breakdown is a list; aggregate dimension_level scores
                breakdown = t.sentiment_breakdown
                if isinstance(breakdown, list) and breakdown:
                    avg = sum(getattr(row, 'sentiment_score', 0) for row in breakdown) / len(breakdown)
                    total_score += avg
                    scored_count += 1
        
        avg_score = (total_score / scored_count * 100) if scored_count else 0
        
        sentiment_label = "Neutral"
        sentiment_type = "neutral"
        if avg_score > 10:
            sentiment_label = "Optimistic"
            sentiment_type = "positive"
        elif avg_score < -10:
            sentiment_label = "Concerning"
            sentiment_type = "negative"
            
        sentiment = {
            "label": sentiment_label,
            "score": f"{'+' if avg_score > 0 else ''}{int(avg_score)}%",
            "text": f"Market sentiment is {sentiment_label.lower()} based on {len(topics)} trending topics.",
            "bar_width": f"{min(100, max(0, 50 + int(avg_score)))}%",
            "type": sentiment_type
        }

        # 2. Trending Context (Top Topic)
        top_topic = topics[0]
        context = {
            "label": getattr(top_topic, 'badge', 'Trending') or "Trending",
            "name": top_topic.title,
            "description": top_topic.description or "Dominating coverage this week."
        }

        # 3. Regional Focus
        regional_topic = next((t for t in topics[1:] if "regional" in (getattr(t, 'category', '') or "").lower()), None)
        if not regional_topic and len(topics) > 1:
            regional_topic = topics[1]
            
        regional = {
            "label": "Regional Focus",
            "name": regional_topic.title if regional_topic else "ECOWAS",
            "description": regional_topic.description if regional_topic else "Monitoring cross-border developments."
        }
        
        return {
            "sentiment": sentiment,
            "context": context,
            "regional": regional
        }

    @staticmethod
    def _fmt_views(n: int) -> str:
        """Format a raw integer view count to a compact string, e.g. 2800 -> '2.8K'."""
        if not n:
            return "0"
        if n >= 1_000_000:
            v = n / 1_000_000
            return (f"{v:.1f}".rstrip("0").rstrip(".") + "M")
        if n >= 1_000:
            v = n / 1_000
            return (f"{v:.1f}".rstrip("0").rstrip(".") + "K")
        return str(n)

    def _enrich_topic_for_frontend(self, topic: Topic) -> Topic:
        """Add frontend-specific fields to topic object (in-memory)."""
        import random  # still used for mock perspective score fallbacks
        from datetime import datetime
        
        # 1. Badge + Category
        title_lower = topic.title.lower()
        if "naira" in title_lower or "bank" in title_lower or "tax" in title_lower or "economy" in title_lower or "inflation" in title_lower or "gdp" in title_lower or "cbn" in title_lower or "forex" in title_lower:
            topic.badge = "Economy"
            if not topic.category:
                topic.category = "Economy"
        elif "governor" in title_lower or "election" in title_lower or "senate" in title_lower or "president" in title_lower or "minister" in title_lower or "government" in title_lower or "fg" in title_lower or "tinubu" in title_lower or "vote" in title_lower:
            topic.badge = "Politics"
            if not topic.category:
                topic.category = "Politics"
        elif "attack" in title_lower or "police" in title_lower or "military" in title_lower or "terror" in title_lower or "kidnap" in title_lower or "bandit" in title_lower:
            topic.badge = "Security"
            if not topic.category:
                topic.category = "Security"
        elif "tech" in title_lower or "startup" in title_lower or "digital" in title_lower or "ai" in title_lower or "app" in title_lower:
            topic.badge = "Technology"
            if not topic.category:
                topic.category = "Technology"
        elif "sport" in title_lower or "football" in title_lower or "soccer" in title_lower or "match" in title_lower or "club" in title_lower or "league" in title_lower or "fifa" in title_lower:
            topic.badge = "Sport"
            if not topic.category:
                topic.category = "Sport"
        elif "business" in title_lower or "company" in title_lower or "market" in title_lower or "trade" in title_lower or "invest" in title_lower:
            topic.badge = "Business"
            if not topic.category:
                topic.category = "Business"
        else:
            topic.badge = topic.category or "Developing"
            if not topic.category:
                topic.category = "General"
             
        # 2. AI Brief and Bullets
        # Priority: executive_summary > summary. For bullets: what_you_need_to_know > facts
        # Safe check for analysis relationship
        analysis = topic.analysis if 'analysis' in topic.__dict__ else None
        
        if analysis and (getattr(analysis, 'executive_summary', None) or getattr(analysis, 'summary', None)):
            topic.ai_brief = getattr(analysis, 'executive_summary', None) or analysis.summary
            topic.bullets = (
                getattr(analysis, 'what_you_need_to_know', None)
                or getattr(analysis, 'facts', None)
                or []
            )
        else:
            # Clean description — strip any internal placeholder text from clustering
            raw_desc = topic.description or ""
            if not raw_desc or raw_desc.lower().startswith("topic driven by") or len(raw_desc) < 30:
                topic.ai_brief = f"Intelligence analysis is being generated for this {(topic.category or 'developing').lower()} story. Key developments and their implications will appear shortly."
            else:
                topic.ai_brief = raw_desc
            # Provide informative fallback bullets
            topic.bullets = [
                "Coverage from multiple sources is being aggregated for this topic.",
                "Sentiment analysis and regional impact assessment are in progress.",
                "Full intelligence brief will be available once analysis is complete."
            ]

            if not topic.analysis:
                topic.analysis = TopicAnalysis(
                    summary=topic.ai_brief,
                    facts=topic.bullets
                )

        now = datetime.utcnow()
        diff = now - (topic.updated_at or topic.created_at)
        seconds = diff.total_seconds()
        if seconds < 3600:
            topic.updated_at_str = f"{int(seconds // 60)} min ago"
        elif seconds < 86400:
            topic.updated_at_str = f"{int(seconds // 3600)} hours ago"
        else:
            topic.updated_at_str = f"{int(seconds // 86400)} days ago"
            
        # 4. Sources (Derived from article_associations)
        flattened_articles = []
        source_counts = {}
        
        if 'article_associations' in topic.__dict__:
            for assoc in topic.article_associations:
                art = assoc.article if 'article' in assoc.__dict__ else None
                if art:
                    art.source_name = getattr(art.source, 'name', "Unknown") if 'source' in art.__dict__ else "Unknown"
                    flattened_articles.append(art)
                    source_counts[art.source_name] = source_counts.get(art.source_name, 0) + 1
        
        topic.articles = flattened_articles
        
        real_source_count = len(source_counts.keys())
        if real_source_count > 0:
            topic.source_count = real_source_count
            
        if real_source_count > 0:
            sources_list = list(source_counts.keys())
            topic.sources = [{"name": s, "bg": "#3498db"} for s in sources_list[:3]]
            if real_source_count > 3:
                topic.sources.append({"name": f"+{real_source_count - 3} more", "bg": "#f39c12"})
        else:
            topic.sources = [
                {"name": "Global News", "bg": "#e74c3c"},
                {"name": "Premium Times", "bg": "#3498db"},
                {"name": "Business Day", "bg": "#2ecc71"},
            ]
            if topic.source_count > 3:
                 topic.sources.append({"name": f"+{topic.source_count - 3} more", "bg": "#f39c12"})        
        # 5. Engagement — use real persisted DB values
        topic.engagement = {
            "comments": topic.comment_count or 0,
            "views": self._fmt_views(topic.view_count or 0),
        }
        
        # 5b. Intelligence Level
        # 'complete' means OpenClaw has finished premium enrichment
        if getattr(topic, 'analysis_status', None) == 'complete':
            topic.intelligence_level = "Premium"
            topic.is_premium = True
        else:
            topic.intelligence_level = "Standard"
            topic.is_premium = False

        # 6. Source Perspectives — use real DB data if available, else generate topic-specific mock
        # Safe check for loaded relationship in async session
        real_perspectives = []
        if 'source_perspectives' in topic.__dict__:
             real_perspectives = list(topic.source_perspectives) if topic.source_perspectives else []
        
        if not real_perspectives:
            # Derive sentiments from topic's own overall_sentiment and score
            overall = (topic.overall_sentiment or "neutral").lower()
            score = topic.sentiment_score or 0.0
            cat = (topic.category or "General").title()
            title_short = topic.title[:35]

            # Scores: local media leans toward overall sentiment; intl is cautious; social is more extreme
            local_pct = int(score * 100) if overall == "positive" else (-int(abs(score) * 60) if overall == "negative" else random.randint(30, 55))
            intl_pct  = int(score * 60)  if overall == "positive" else (-int(abs(score) * 40) if overall == "negative" else random.randint(20, 45))
            social_pct = int(score * 120) if overall == "positive" else (-int(abs(score) * 90) if overall == "negative" else random.randint(-20, 30))
            # Clamp to [-99, 99]
            local_pct  = max(-99, min(99, local_pct))
            intl_pct   = max(-99, min(99, intl_pct))
            social_pct = max(-99, min(99, social_pct))

            def pct_str(v): return f"+{v}%" if v >= 0 else f"{v}%"
            def sent(v): return "positive" if v > 15 else ("negative" if v < -15 else "neutral")

            mock_perspectives = [
                {
                    "source_name": "Local Media",
                    "source_type": "Mainstream",
                    "sentiment": sent(local_pct),
                    "sentiment_percentage": pct_str(local_pct),
                    "key_narrative": f"Local outlets highlight domestic implications of {title_short}.",
                    "frame_label": "Local Lens"
                },
                {
                    "source_name": "Intl. Press",
                    "source_type": "International",
                    "sentiment": sent(intl_pct),
                    "sentiment_percentage": pct_str(intl_pct),
                    "key_narrative": f"International coverage focuses on {cat} sector policy ramifications.",
                    "frame_label": "Global View"
                },
                {
                    "source_name": "Social Media",
                    "source_type": "Public",
                    "sentiment": sent(social_pct),
                    "sentiment_percentage": pct_str(social_pct),
                    "key_narrative": f"Public discourse reflects {overall} sentiment on {cat} outlook.",
                    "frame_label": "Public Pulse"
                },
            ]
            object.__setattr__(topic, '_perspectives_data', mock_perspectives)
        else:
            object.__setattr__(topic, '_perspectives_data', real_perspectives)

        # 7. Regional Impacts — use real DB data if available, else generate topic-specific mock
        real_impacts = []
        if 'regional_impacts' in topic.__dict__:
             real_impacts = list(topic.regional_impacts) if topic.regional_impacts else []

        if not real_impacts:
            cat = (topic.category or "General").title()
            overall = (topic.overall_sentiment or "neutral").lower()
            title_short = topic.title[:35]

            # Build impact data contextual to this topic's category
            cat_lower = cat.lower()
            if "economy" in cat_lower or "business" in cat_lower or "finance" in cat_lower:
                mock_impacts = [
                    {"impact_category": "Economic", "icon": "💰", "title": "Market Effect", "value": f"Volatility expected in {cat} sector", "severity": "high", "context": f"Related to: {title_short}"},
                    {"impact_category": "Trade",    "icon": "📊", "title": "Trade Impact",  "value": "Supply chains under watch",         "severity": "medium", "context": "Cross-border commerce affected."},
                    {"impact_category": "Consumer", "icon": "🛒", "title": "Consumer Cost", "value": "Price pressure likely near-term",   "severity": "medium", "context": "Inflation pass-through risk."},
                ]
            elif "politics" in cat_lower or "government" in cat_lower:
                mock_impacts = [
                    {"impact_category": "Policy",      "icon": "⚖️",  "title": "Policy Shift",    "value": "Legislative review possible",    "severity": "high",   "context": f"Related to: {title_short}"},
                    {"impact_category": "Governance",  "icon": "🏛️", "title": "Governance",      "value": "Institutional response pending",  "severity": "medium", "context": "Oversight committees on notice."},
                    {"impact_category": "Public Trust","icon": "🗳️", "title": "Public Sentiment","value": f"{overall.title()} public mood", "severity": "low",    "context": "Polling data being reviewed."},
                ]
            elif "security" in cat_lower:
                mock_impacts = [
                    {"impact_category": "Safety",    "icon": "🛡️", "title": "Security Alert",   "value": "Heightened vigilance advised",     "severity": "high",   "context": f"Related to: {title_short}"},
                    {"impact_category": "Military",  "icon": "⚔️",  "title": "Defense Posture", "value": "Response protocols activated",    "severity": "high",   "context": "Joint forces on standby."},
                    {"impact_category": "Civilians", "icon": "🏘️", "title": "Civil Impact",     "value": "Displacement risk being assessed", "severity": "medium", "context": "Humanitarian monitoring underway."},
                ]
            elif "tech" in cat_lower or "technology" in cat_lower:
                mock_impacts = [
                    {"impact_category": "Innovation", "icon": "💡", "title": "Tech Landscape", "value": "Disruption potential high",         "severity": "medium", "context": f"Related to: {title_short}"},
                    {"impact_category": "Digital",    "icon": "📡", "title": "Digital Shift",  "value": "Adoption curve accelerating",      "severity": "low",    "context": "Infrastructure investment rising."},
                    {"impact_category": "Jobs",       "icon": "👷", "title": "Workforce",      "value": "Skills gap under spotlight",       "severity": "medium", "context": "Retraining programmes discussed."},
                ]
            else:
                mock_impacts = [
                    {"impact_category": "Social",     "icon": "🗣️", "title": "Social Impact",  "value": f"Community response to {cat} news", "severity": "medium", "context": f"Public debate on {title_short}."},
                    {"impact_category": "Regulatory", "icon": "📋", "title": "Regulatory",    "value": "Policy makers taking note",          "severity": "low",    "context": "Committees reviewing implications."},
                    {"impact_category": "Regional",   "icon": "🌍", "title": "Regional Reach","value": "Cross-border interest growing",     "severity": "low",    "context": "ECOWAS bloc monitoring closely."},
                ]
            object.__setattr__(topic, '_impacts_data', mock_impacts)
        else:
            object.__setattr__(topic, '_impacts_data', real_impacts)
        
        return topic

    async def get_trending_topics(self, page: int = 1, limit: int = 20, filter_type: str = "all", category: Optional[str] = None, region: Optional[str] = None) -> Tuple[List[Topic], int]:
        """Fetch trending topics with pagination and filtering."""
        from datetime import datetime, timedelta
        
        from sqlalchemy.orm import make_transient

        offset = (page - 1) * limit
        query = select(Topic).options(
             selectinload(Topic.article_associations).joinedload(TopicArticle.article).joinedload(RawArticle.source),
             selectinload(Topic.regional_categories)
        )
        
        # CRITICAL: Return topics regardless of status so cards show up
        # Only exclude archived/error topics
        query = query.where(Topic.status.notin_(['archived', 'error']))
        
        # Apply category filter
        if category and category.lower() != "all":
            query = query.where(func.lower(Topic.category) == category.lower())
        
        # Apply region filter
        if region and region.lower() != "all":
            query = query.join(TopicRegionalCategory).where(func.lower(TopicRegionalCategory.region_name) == region.lower())
        
        # Apply time/status filters
        
        # Apply filters
        now = datetime.utcnow()
        if filter_type == "today":
            query = query.where(Topic.updated_at >= now - timedelta(days=1))
        elif filter_type == "week":
            query = query.where(Topic.updated_at >= now - timedelta(weeks=1))
        elif filter_type == "month":
            query = query.where(Topic.updated_at >= now - timedelta(days=30))
        elif filter_type == "developing":
             # Topics with developing status OR trending
             query = query.where(or_(Topic.status == "developing", Topic.is_trending == True))
        
        # Count total — build a fresh count query to avoid whereclause issues
        count_q = select(func.count(Topic.id)).where(Topic.status.notin_(['archived', 'error']))
        if category and category.lower() != "all":
            count_q = count_q.where(func.lower(Topic.category) == category.lower())
        
        if region and region.lower() != "all":
            count_q = count_q.join(TopicRegionalCategory).where(func.lower(TopicRegionalCategory.region_name) == region.lower())
        
        if filter_type == "today":
            count_q = count_q.where(Topic.updated_at >= now - timedelta(days=1))
        elif filter_type == "week":
            count_q = count_q.where(Topic.updated_at >= now - timedelta(weeks=1))
        elif filter_type == "month":
            count_q = count_q.where(Topic.updated_at >= now - timedelta(days=30))
        elif filter_type == "developing":
             count_q = count_q.where(or_(Topic.status == "developing", Topic.is_trending == True))

        total = (await self.db.execute(count_q)).scalar() or 0

        # Fetch items
        items_query = (
            query
            .order_by(desc(Topic.updated_at))
            .offset(offset)
            .limit(limit)
        )
        items = (await self.db.execute(items_query)).unique().scalars().all()
        
        # Detach topics from session so _enrich can mutate attributes safely
        for t in items:
            self.db.expunge(t)
            make_transient(t)

        # Enrich items
        enriched_items = [self._enrich_topic_for_frontend(t) for t in items]

        return enriched_items, total


    async def get_vertical_articles(self, category: str, page: int = 1, limit: int = 20) -> Tuple[List[RawArticle], int]:
        """Fetch articles for a specific vertical/category with pagination."""
        offset = (page - 1) * limit

        # Count total
        count_query = select(func.count(RawArticle.id)).where(RawArticle.category == category)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch items
        items_query = (
            select(RawArticle, Source.name.label("source_name"))
            .join(Source)
            .where(RawArticle.category == category)
            .order_by(desc(RawArticle.published_at))
            .offset(offset)
            .limit(limit)
        )
        items_result = await self.db.execute(items_query)
        items = []
        for row in items_result:
            article = row.RawArticle
            article.source_name = row.source_name
            items.append(article)

        return items, total

    async def get_topic_detail(self, topic_id: int) -> Optional[Topic]:
        """Fetch full topic detail with all related data."""
        from fastapi import HTTPException
        
        query = (
            select(Topic)
            .options(
                selectinload(Topic.analysis),
                selectinload(Topic.sentiment_breakdown),
                selectinload(Topic.source_perspectives),
                selectinload(Topic.regional_impacts),
                selectinload(Topic.intelligence_card),
                selectinload(Topic.trends),
                selectinload(Topic.videos),
                selectinload(Topic.article_associations).joinedload(TopicArticle.article).joinedload(RawArticle.source)
            )
            .where(Topic.id == topic_id)
        )
        result = await self.db.execute(query)
        topic = result.unique().scalar_one_or_none()
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Flatten articles for the schema
        topic.articles = []
        for assoc in topic.article_associations:
            article = assoc.article
            article.source_name = article.source.name
            topic.articles.append(article)
            
        from sqlalchemy.orm import make_transient
        self.db.expunge(topic)
        make_transient(topic)
        topic = self._enrich_topic_for_frontend(topic)
        
        # NOTE: view_count is incremented exclusively via POST /api/topic/{id}/view
        # Do NOT increment here — that caused double-counting with the flyout pattern.
        return topic

    async def search_topics(self, query: str, page: int = 1, limit: int = 10) -> Tuple[List[dict], int]:
        """Search processed topics by title and description. Returns dicts with engagement data."""
        from datetime import datetime
        offset = (page - 1) * limit
        search_filter = or_(
            Topic.title.ilike(f"%{query}%"),
            Topic.description.ilike(f"%{query}%"),
        )
        # Exclude archived/error topics
        base_filter = Topic.status.notin_(["archived", "error"])

        count_query = select(func.count(Topic.id)).where(base_filter, search_filter)
        total = (await self.db.execute(count_query)).scalar() or 0

        items_query = (
            select(Topic)
            .options(selectinload(Topic.analysis))
            .where(base_filter, search_filter)
            .order_by(desc(Topic.updated_at))
            .offset(offset)
            .limit(limit)
        )
        topics = (await self.db.execute(items_query)).unique().scalars().all()

        def rel_time(dt):
            if not dt:
                return "Recently"
            diff = datetime.utcnow() - dt
            s = diff.total_seconds()
            if s < 3600: return f"{int(s // 60)} min ago"
            if s < 86400: return f"{int(s // 3600)}h ago"
            return f"{int(s // 86400)}d ago"

        results = []
        for t in topics:
            brief = ""
            if t.analysis and t.analysis.summary:
                brief = t.analysis.summary[:200]
            elif t.description:
                brief = t.description[:200]
            results.append({
                "id": t.id,
                "title": t.title,
                "category": t.category or "General",
                "brief": brief,
                "view_count": t.view_count or 0,
                "views_count": t.view_count or 0,
                "comment_count": t.comment_count or 0,
                "comments_count": t.comment_count or 0,
                "updated_at_str": rel_time(t.updated_at),
                "slug": t.title.lower().replace(" ", "-"),
            })
        return results, total

    async def search_articles(self, query: str, page: int = 1, limit: int = 20) -> Tuple[List[RawArticle], int]:
        """Basic text search for articles."""
        offset = (page - 1) * limit
        search_filter = or_(
            RawArticle.title.ilike(f"%{query}%"),
            RawArticle.content.ilike(f"%{query}%")
        )

        # Count total
        count_query = select(func.count(RawArticle.id)).where(search_filter)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Fetch items
        items_query = (
            select(RawArticle, Source.name.label("source_name"))
            .join(Source)
            .where(search_filter)
            .order_by(desc(RawArticle.published_at))
            .offset(offset)
            .limit(limit)
        )
        items_result = await self.db.execute(items_query)
        items = []
        for row in items_result:
            article = row.RawArticle
            article.source_name = row.source_name
            items.append(article)

        return items, total

    async def get_article_detail(self, article_id: int) -> Optional[RawArticle]:
        """Fetch a single article by ID with source info."""
        query = (
            select(RawArticle, Source.name.label("source_name"))
            .join(Source)
            .where(RawArticle.id == article_id)
        )
        result = await self.db.execute(query)
        row = result.first()
        
        if row:
            article = row.RawArticle
            article.source_name = row.source_name
            return article
        return None

    async def get_topic_by_title(self, title: str) -> Optional[Topic]:
        """Fetch full topic detail by title (case-insensitive)."""
        query = (
            select(Topic)
            .options(
                joinedload(Topic.analysis),
                joinedload(Topic.sentiment_breakdown),
                joinedload(Topic.source_perspectives),
                joinedload(Topic.regional_impacts),
                joinedload(Topic.intelligence_card),
                joinedload(Topic.trends),
                joinedload(Topic.videos),
                joinedload(Topic.article_associations).joinedload(TopicArticle.article).joinedload(RawArticle.source)
            )
            .where(func.lower(Topic.title) == func.lower(title))
        )
        result = await self.db.execute(query)
        topic = result.unique().scalar_one_or_none()
        
        if topic:
            # Flatten articles for the schema
            topic.articles = []
            for assoc in topic.article_associations:
                article = assoc.article
                article.source_name = article.source.name
                topic.articles.append(article)
                
            from sqlalchemy.orm import make_transient
            self.db.expunge(topic)
            make_transient(topic)
            topic = self._enrich_topic_for_frontend(topic)
                
        return topic

    async def get_vertical_data(self, category: str) -> dict:
        """Fetch data for a specific vertical page (trending topics + articles)."""
        
        # 1. Topics for this Vertical (Trending first, then latest)
        query = (
            select(Topic)
            .options(
                 joinedload(Topic.analysis),
                 joinedload(Topic.sentiment_breakdown),
                 joinedload(Topic.article_associations).joinedload(TopicArticle.article).joinedload(RawArticle.source)
            )
            .where(func.lower(Topic.category) == func.lower(category))
            .order_by(desc(Topic.is_trending), desc(Topic.updated_at))
            .limit(10)
        )
        topics = (await self.db.execute(query)).unique().scalars().all()
        
        # Fallback: if no topics for this vertical, try "related" or just latest generic
        if not topics and category.lower() in ["economy", "business"]:
             # these are close, maybe mixed? For now, fallback to all trending
             pass

        # Detach topics from session so _enrich can mutate attributes safely
        from sqlalchemy.orm import make_transient
        for t in topics:
            self.db.expunge(t)
            make_transient(t)

        # Enrich topics
        enriched_topics = [self._enrich_topic_for_frontend(t) for t in topics]

        # 2. Latest Articles for this Vertical
        latest_articles_query = (
            select(RawArticle, Source.name.label("source_name"))
            .join(Source)
            .where(func.lower(RawArticle.category) == func.lower(category))
            .order_by(desc(RawArticle.published_at))
            .limit(10)
        )
        latest_articles_result = await self.db.execute(latest_articles_query)
        latest_articles = []
        for row in latest_articles_result:
            article = row.RawArticle
            article.source_name = row.source_name
            latest_articles.append(article)
            
        # 3. Pulse Data for this Vertical
        pulse = self._get_pulse_data(enriched_topics) if enriched_topics else None

        # 4. Vertical Stats (Dynamic)
        count_topics_query = select(func.count(Topic.id)).where(func.lower(Topic.category) == func.lower(category))
        total_active_topics = (await self.db.execute(count_topics_query)).scalar() or 0
        
        count_sources_query = select(func.count(func.distinct(RawArticle.source_id))).where(func.lower(RawArticle.category) == func.lower(category))
        total_category_sources = (await self.db.execute(count_sources_query)).scalar() or 0

        stats = {
            "active_topics": total_active_topics,
            "total_sources": total_category_sources,
            "total_views": sum((t.view_count or 0) for t in enriched_topics),
            "update_freq": "Real-time"
        }

        return {
            "topics": enriched_topics,
            "featured_articles": latest_articles,
            "category": category,
            "pulse": pulse,
            "stats": stats
        }
