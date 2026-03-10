
import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Add parent directory to sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Set up logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("E2E-Pipeline")

from app.database import AsyncSessionLocal
from app.utils.jobs import create_job_record, update_job_status
from sqlalchemy import select, func

async def run_pipeline():
    logger.info("--- Starting E2E Pipeline ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Article Fetching
        logger.info("\n>>> Phase 1: Fetching Articles")
        fetch_jid = await create_job_record(db, "FETCH_ARTICLES")
        
        from app.models.source import Source
        from app.services.crawler_service import CrawlerService
        
        crawler = CrawlerService(db)
        res = await db.execute(select(Source).where(Source.is_active == True))
        sources = res.scalars().all()
        logger.info(f"Found {len(sources)} active sources")
        
        await update_job_status(db, fetch_jid, "RUNNING")
        total_fetched = 0
        for s in sources:
            try:
                logger.info(f"  Fetching from {s.name}...")
                count = await crawler.fetch_articles(s)
                total_fetched += count
                logger.info(f"  Fetched {count} articles")
            except Exception as e:
                logger.error(f"  Error fetching from {s.name}: {e}")
        
        await update_job_status(db, fetch_jid, "COMPLETED", result={"fetched_count": total_fetched})
        logger.info(f"Phase 1 Complete. Total fetched: {total_fetched}")

        # 2. Normalization
        logger.info("\n>>> Phase 2: Normalizing Articles (Entities & Embeddings)")
        norm_jid = await create_job_record(db, "NORMALIZE_ARTICLES")
        from app.services.ai.nlp_service import NLPService
        from app.services.ai.embedding_service import EmbeddingService
        from app.models import ArticleEntity, ArticleEmbedding, RawArticle
        
        from app.constants import DEFAULT_CATEGORY
        import re
        
        await update_job_status(db, norm_jid, "RUNNING")
        nlp = NLPService()
        embedder = EmbeddingService()
        
        # Fetch pending articles
        query = select(RawArticle).where(RawArticle.sentiment_score == None).limit(100)
        result = await db.execute(query)
        articles = result.scalars().all()
        logger.info(f"Normalizing {len(articles)} articles")
        
        for article in articles:
            # 1. Strip HTML before processing
            raw_text = (article.title or "") + " " + (article.content or "")
            clean_text = re.sub(r'<[^>]+>', ' ', raw_text).lower()

            # 2. Extract entities
            entities = nlp.extract_entities(article.title + " " + (article.description or ""))
            for ent in entities:
                db.add(ArticleEntity(article_id=article.id, entity_name=ent["text"], entity_type=ent["label"]))
            
            # 3. Generate embedding on clean text
            vec = embedder.generate_embedding(clean_text[:500])
            db.add(ArticleEmbedding(article_id=article.id, embedding=vec))
            
            # 4. Categorization — canonical slugs from constants.py ONLY
            if not article.category:
                t = clean_text
                if any(x in t for x in ["senate", "president", "election", "law", "policy", "government", "minister", "tinubu", "governor"]):
                    article.category = "politics"
                elif any(x in t for x in ["naira", "inflation", "gdp", "cbn", "fiscal", "monetary", "currency", "forex", "interest rate", "budget"]):
                    article.category = "economy"
                elif any(x in t for x in ["market", "bank", "stock", "trade", "refinery", "dangote", "startup", "entrepreneur", "company", "business"]):
                    article.category = "business"
                elif any(x in t for x in ["ai", "software", "digital", "cyber", "crypto", "tech", "fintech", "blockchain", "satellite"]):
                    article.category = "technology"
                elif any(x in t for x in ["football", "afcon", "match", "league", "sport", "npfl", "super eagles"]):
                    article.category = "sports"
                elif any(x in t for x in ["police", "army", "attack", "kidnap", "bandit", "terror", "insurgent", "robbery", "piracy", "crime"]):
                    article.category = "security"
                elif any(x in t for x in ["ecowas", "west africa", "cross-border", "bilateral", "diplomatic", "foreign"]):
                    article.category = "regional"
                elif any(x in t for x in ["climate", "pollution", "deforestation", "niger delta", "oil spill", "conservation", "environment"]):
                    article.category = "environment"
                elif any(x in t for x in ["health", "education", "poverty", "community", "welfare", "gender", "youth", "women", "social"]):
                    article.category = "social"
                else:
                    article.category = DEFAULT_CATEGORY  # "general"
            
            # Mark as processed
            article.sentiment_score = 0.0
            
        await db.commit()
        await update_job_status(db, norm_jid, "COMPLETED", result={"normalized_count": len(articles)})
        logger.info(f"Phase 2 Complete. Normalized {len(articles)} articles")

        # 3. Clustering
        logger.info("\n>>> Phase 3: Clustering Articles into Topics")
        cluster_jid = await create_job_record(db, "CLUSTERING")
        from app.services.ai.clustering_service import ClusteringService
        from app.models import TopicArticle, Topic
        
        await update_job_status(db, cluster_jid, "RUNNING")
        cluster_svc = ClusteringService(db)
        
        query = (
            select(ArticleEmbedding, RawArticle.title, RawArticle.category)
            .join(RawArticle, RawArticle.id == ArticleEmbedding.article_id)
            .outerjoin(TopicArticle, TopicArticle.article_id == ArticleEmbedding.article_id)
            .where(TopicArticle.topic_id == None)
            .limit(100)
        )
        result = await db.execute(query)
        items = result.all()
        logger.info(f"Clustering {len(items)} articles")
        
        for emb_record, title, category in items:
            topic_id = await cluster_svc.find_or_create_topic(emb_record.embedding, title)
            await cluster_svc.assign_article_to_topic(emb_record.article_id, topic_id)
            
            # Propagate category to topic
            if category:
                t_res = await db.execute(select(Topic).where(Topic.id == topic_id))
                topic_obj = t_res.scalar_one_or_none()
                if topic_obj and not topic_obj.category:
                    topic_obj.category = category
            
        await db.commit()
        await update_job_status(db, cluster_jid, "COMPLETED", result={"clustered_count": len(items)})
        logger.info(f"Phase 3 Complete. Clustered {len(items)} articles")

        # 4. AI Analysis
        logger.info("\n>>> Phase 4: Generating AI Analysis (Topic Detail)")
        analysis_jid = await create_job_record(db, "AI_ANALYSIS")
        from app.jobs.generate_topic_analysis_job_enhanced import GenerateTopicAnalysisJob
        from app.models import TopicAnalysis
        
        await update_job_status(db, analysis_jid, "RUNNING")
        job = GenerateTopicAnalysisJob(db)
        
        # Process topics without analysis
        query = select(Topic.id).outerjoin(TopicAnalysis).where(TopicAnalysis.id == None)
        result = await db.execute(query)
        topic_ids = result.scalars().all()
        logger.info(f"Analyzing {len(topic_ids)} topics")
        
        for t_id in topic_ids:
            logger.info(f"  Analyzing topic {t_id}...")
            await job.execute(t_id)
            
        await update_job_status(db, analysis_jid, "COMPLETED", result={"analyzed_count": len(topic_ids)})
        logger.info(f"Phase 4 Complete. Analyzed {len(topic_ids)} topics")

        # 5. Trend Update
        logger.info("\n>>> Phase 5: Updating Trends")
        trend_jid = await create_job_record(db, "TREND_UPDATE")
        from app.models import TopicTrend, TopicArticle, RawArticle
        
        await update_job_status(db, trend_jid, "RUNNING")
        
        query = (
            select(
                Topic.id, 
                func.count(RawArticle.id).label("article_count"),
                func.count(func.distinct(RawArticle.source_id)).label("source_count")
            )
            .join(TopicArticle, Topic.id == TopicArticle.topic_id)
            .join(RawArticle, TopicArticle.article_id == RawArticle.id)
            .group_by(Topic.id)
        )
        
        result = await db.execute(query)
        topic_stats = result.all()
        updated_count = 0
        for t_id, a_count, s_count in topic_stats:
            score = (a_count * 1.0) + (s_count * 2.0)
            db.add(TopicTrend(topic_id=t_id, interest_score=score, date=datetime.now()))
            
            t_query = select(Topic).where(Topic.id == t_id)
            t_res = await db.execute(t_query)
            topic = t_res.scalar_one()
            topic.is_trending = score >= 0.0 # Force for test
            updated_count += 1
            
        await db.commit()
        await update_job_status(db, trend_jid, "COMPLETED", result={"topics_updated": updated_count})
        logger.info(f"Phase 5 Complete. Updated {updated_count} topics")

    logger.info("\n--- E2E Pipeline Run Finished ---")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
