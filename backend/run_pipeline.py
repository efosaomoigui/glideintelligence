"""
run_pipeline.py
🚀 ENHANCED: Runs the full pipeline with smart features.
  1. fetch_articles  → raw_articles
  2. normalize       → embeddings + article categories
  3. cluster         → topics (with category propagation)
  4. ai_analysis     → summaries, sentiment, impacts, cards

New Features (Step 4):
- Parallel processing (process N topics at once)
- Batch optimization (groups by category)
- Real-time monitoring (cost, speed, success rate)
- Budget enforcement (stops at daily limit)
- Progress tracking
"""

import asyncio
from sqlalchemy import select, or_, text
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
from app.services.ai.content_generator import RateLimiter, CostTracker
import logging
import time
from datetime import datetime
from collections import defaultdict
import os
import argparse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PipelineMonitor:
    """Real-time monitoring of pipeline performance."""
    
    def __init__(self):
        self.start_time = time.time()
        self.topics_processed = 0
        self.topics_succeeded = 0
        self.topics_failed = 0
        self.by_category = defaultdict(lambda: {'success': 0, 'failed': 0})
        self.durations = []
    
    def record_success(self, category: str, duration: float):
        self.topics_processed += 1
        self.topics_succeeded += 1
        self.by_category[category]['success'] += 1
        self.durations.append(duration)
    
    def record_failure(self, category: str):
        self.topics_processed += 1
        self.topics_failed += 1
        self.by_category[category]['failed'] += 1
    
    def print_summary(self, cost_tracker: CostTracker):
        """Print detailed summary."""
        runtime = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("PIPELINE EXECUTION SUMMARY".center(80))
        print("="*80)
        
        print(f"\n[PERFORMANCE] PERFORMANCE")
        print(f"   Total topics:        {self.topics_processed}")
        print(f"   Successful:          {self.topics_succeeded} [OK]")
        print(f"   Failed:              {self.topics_failed} [FAIL]")
        print(f"   Success rate:        {(self.topics_succeeded/max(1, self.topics_processed)*100):.1f}%")
        print(f"   Runtime:             {runtime:.1f}s")
        
        if self.durations:
            avg_duration = sum(self.durations) / len(self.durations)
            print(f"   Avg time/topic:      {avg_duration:.1f}s")
            print(f"   Topics/minute:       {(self.topics_processed / (runtime / 60)):.1f}")
        
        print(f"\n[COST] COST")
        print(f"   Tokens used:         {cost_tracker.tokens_used:,}")
        print(f"   Today's spend:       ${cost_tracker.get_today_cost():.4f}")
        
        if cost_tracker.costs_by_provider:
            print(f"\n   By provider:")
            for provider, cost in cost_tracker.costs_by_provider.items():
                pct = (cost / cost_tracker.get_today_cost() * 100) if cost_tracker.get_today_cost() > 0 else 0
                print(f"      {provider:12s}  ${cost:.4f} ({pct:.1f}%)")
        
        if self.by_category:
            print(f"\n[BY CATEGORY] BY CATEGORY")
            for category, stats in sorted(self.by_category.items()):
                total = stats['success'] + stats['failed']
                success_rate = (stats['success'] / total * 100) if total > 0 else 0
                print(f"   {category:12s}  {stats['success']}/{total} ({success_rate:.0f}%)")
        
        print("\n" + "="*80 + "\n")

async def step1_fetch():
    print("\n=== STEP 1: Fetching articles ===")
    from app.models.source import Source
    from app.services.crawler_service import CrawlerService
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Source).where(Source.is_active == True))
        sources = res.scalars().all()
        print(f"  Found {len(sources)} active sources")
        crawler = CrawlerService(db)
        total = 0
        for s in sources:
            try:
                count = await crawler.fetch_articles(s)
                print(f"  [{s.name}] fetched {count} articles")
                total += count
            except Exception as e:
                print(f"  [{s.name}] ERROR: {e}")
        print(f"[OK] Total fetched: {total} articles")
        return total

async def step2_normalize():
    print("\n=== STEP 2: Normalizing articles ===")
    from app.services.ai.nlp_service import NLPService
    from app.services.ai.embedding_service import EmbeddingService
    from app.models import ArticleEntity, ArticleEmbedding, RawArticle
    from app.constants import DEFAULT_CATEGORY
    import re
    async with AsyncSessionLocal() as db:
        nlp = NLPService()
        embedder = EmbeddingService()
        # Process all unnormalized articles in batches or without limit
        query = select(RawArticle).where(RawArticle.sentiment_score == None)
        result = await db.execute(query)
        articles = result.scalars().all()
        print(f"  Processing {len(articles)} unnormalized articles...")
        for article in articles:
            # Strip HTML before embedding and save in db
            raw_title = article.title or ""
            raw_content = article.content or ""
            
            clean_title = re.sub(r'<[^>]+>', ' ', raw_title)
            clean_content = re.sub(r'<[^>]+>', ' ', raw_content)
            
            # Update content to be free of HTML residue
            article.content = clean_content.strip()

            clean_text = (clean_title + " " + clean_content).lower()
            
            # Entities
            entities = nlp.extract_entities(raw_title + " " + (article.description or ""))
            for ent in entities:
                db.add(ArticleEntity(article_id=article.id, entity_name=ent["text"], entity_type=ent["label"]))
            
            # Embedding on clean text
            vec = embedder.generate_embedding(clean_text[:500])
            db.add(ArticleEmbedding(article_id=article.id, embedding=vec))
            article.sentiment_score = 0.0  # mark as processed
            # Category — canonical slugs from constants.py ONLY
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
                    article.category = "sport"
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
        await db.commit()
        print(f"[OK] Normalized {len(articles)} articles")
        return len(articles)

async def step3_cluster():
    print("\n=== STEP 3: Clustering into topics ===")
    from app.services.ai.clustering_service import ClusteringService
    from app.models import ArticleEmbedding, RawArticle, TopicArticle, Topic
    async with AsyncSessionLocal() as db:
        query = (
            select(ArticleEmbedding, RawArticle.title)
            .join(RawArticle, RawArticle.id == ArticleEmbedding.article_id)
            .outerjoin(TopicArticle, TopicArticle.article_id == ArticleEmbedding.article_id)
            .where(TopicArticle.topic_id == None)
            .limit(100)
        )
        result = await db.execute(query)
        items = result.all()
        print(f"  Clustering {len(items)} unclustered articles...")
        cluster_svc = ClusteringService(db)
        for emb_record, title in items:
            topic_id = await cluster_svc.find_or_create_topic(emb_record.embedding, title)
            await cluster_svc.assign_article_to_topic(emb_record.article_id, topic_id)
            # Propagate category from article to topic
            art_res = await db.execute(select(RawArticle).where(RawArticle.id == emb_record.article_id))
            article = art_res.scalar_one_or_none()
            if article and article.category:
                t_res = await db.execute(select(Topic).where(Topic.id == topic_id))
                topic_obj = t_res.scalar_one_or_none()
                if topic_obj and not topic_obj.category:
                    topic_obj.category = article.category.lower()
        await db.commit()
        # Report
        t_res = await db.execute(select(Topic))
        topics = t_res.scalars().all()
        with_cat = [t for t in topics if t.category]
        print(f"[OK] Topics created: {len(topics)} | with category: {len(with_cat)}")
        if topics[:3]:
            for t in topics[:3]:
                topic_cat = t.category if t.category else "unknown"
                print(f"    - [{topic_cat}] {t.title[:60]}")
        return len(topics)

async def step4_ai_analysis():
    """Enhanced AI analysis with smart features."""
    
    print("\n" + "="*80)
    print("ENHANCED AI ANALYSIS PIPELINE".center(80))
    print("="*80)
    
    # Configuration
    MAX_PARALLEL = int(os.getenv('MAX_PARALLEL_TOPICS', '3'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
    DAILY_BUDGET = float(os.getenv('DAILY_BUDGET_USD', '5.0'))
    BATCH_BY_CATEGORY = os.getenv('BATCH_BY_CATEGORY', 'true').lower() == 'true'
    
    print(f"\n[CONFIG] CONFIGURATION")
    print(f"   Max parallel:        {MAX_PARALLEL} topics")
    print(f"   Batch size:          {BATCH_SIZE} topics")
    print(f"   Daily budget:        ${DAILY_BUDGET:.2f}")
    print(f"   Batch by category:   {BATCH_BY_CATEGORY}")
    print()
    
    # Initialize tracking
    rate_limiter = RateLimiter()
    cost_tracker = CostTracker()
    monitor = PipelineMonitor()
    
    # Semaphore for parallel processing
    semaphore = asyncio.Semaphore(MAX_PARALLEL)
    
    async def process_one_topic(topic_id, title, category, db):
        """Process a single topic with tracking."""
        async with semaphore:
            start = time.time()
            cat = category or "unknown"
            
            try:
                logger.info(f"START Processing [{cat}] {title[:50]}...")
                
                # We need a fresh session-like access or we pass the db safely
                # But sqlalchemy usually wants unique sessions per thread/task if they do writes
                # For simplicity here we assume the DB handle is okay or we could create a new session
                async with AsyncSessionLocal() as item_db:
                    job = GenerateTopicAnalysisJob(item_db, rate_limiter, cost_tracker)
                    await job.execute(topic_id)
                
                duration = time.time() - start
                monitor.record_success(cat, duration)
                logger.info(f"DONE Completed in {duration:.1f}s")
                
            except Exception as e:
                monitor.record_failure(cat)
                logger.error(f"FAIL Failed: {str(e)[:100]}")
    
    async with AsyncSessionLocal() as db:
        # Fetch pending topics (not yet stable)
        query = select(Topic).where(
            Topic.status != 'stable',
            Topic.category != None
        ).limit(BATCH_SIZE)
        
        result = await db.execute(query)
        topics = result.scalars().all()
        
        if not topics:
            print("[INFO] No pending topics to process")
            return
        
        print(f"[INFO] Found {len(topics)} topics to process")
        
        # Group by category if enabled
        if BATCH_BY_CATEGORY:
            by_category = defaultdict(list)
            for topic in topics:
                by_category[topic.category or "unknown"].append(topic)
            
            print(f"\n[BATCH] BATCHING BY CATEGORY")
            for cat, cat_topics in sorted(by_category.items()):
                print(f"   {cat:12s}  {len(cat_topics)} topics")
            print()
            
            # Process category by category
            for category, cat_topics in sorted(by_category.items()):
                print(f"\n[RUN] Processing {category} category ({len(cat_topics)} topics)...")
                
                # Check budget before each category
                if not cost_tracker.can_process(DAILY_BUDGET):
                    print(f"[WARN] Daily budget reached (${cost_tracker.get_today_cost():.2f} / ${DAILY_BUDGET:.2f})")
                    print(f"   Stopping pipeline")
                    break
                
                # Process topics in parallel within category
                tasks = [process_one_topic(t.id, t.title, t.category, db) for t in cat_topics]
                await asyncio.gather(*tasks)
                
                print(f"[OK] {category} category complete")
        
        else:
            # Process all topics in parallel (no grouping)
            print(f"\n[RUN] Processing all topics in parallel...")
            
            tasks = []
            for topic in topics:
                # Check budget before each topic
                if not cost_tracker.can_process(DAILY_BUDGET):
                    print(f"[WARN] Daily budget reached (${cost_tracker.get_today_cost():.2f} / ${DAILY_BUDGET:.2f})")
                    break
                
                tasks.append(process_one_topic(topic.id, topic.title, topic.category, db))
            
            await asyncio.gather(*tasks)
    
    # Print final summary
    monitor.print_summary(cost_tracker)
    
    print("[OK] AI analysis step complete")

async def main():
    """Main pipeline orchestrator."""
    parser = argparse.ArgumentParser(description="Run the backend pipeline steps.")
    parser.add_argument(
        "--steps", 
        type=str, 
        default="fetch,normalize,cluster,analysis",
        help="Comma-separated steps to run: fetch,normalize,cluster,analysis"
    )
    args = parser.parse_args()
    steps = args.steps.split(",")
    
    if "fetch" in steps:
        await step1_fetch()
    
    if "normalize" in steps:
        await step2_normalize()
        
    if "cluster" in steps:
        await step3_cluster()
    
    if "analysis" in steps:
        await step4_ai_analysis()
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETE".center(80))
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
