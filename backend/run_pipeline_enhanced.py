"""
run_pipeline_enhanced.py
🚀 ENHANCED: Runs the full pipeline with smart features.

New Features:
- Parallel processing (process N topics at once)
- Batch optimization (groups by category)
- Real-time monitoring (cost, speed, success rate)
- Budget enforcement (stops at daily limit)
- Progress tracking
"""

import asyncio
from sqlalchemy import select, or_
from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
from app.services.ai.content_generator import RateLimiter, CostTracker
import logging
import time
from datetime import datetime
from collections import defaultdict
import os

logging.basicConfig(level=logging.INFO)
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
        
        print(f"\n📊 PERFORMANCE")
        print(f"   Total topics:        {self.topics_processed}")
        print(f"   Successful:          {self.topics_succeeded} ✅")
        print(f"   Failed:              {self.topics_failed} ❌")
        print(f"   Success rate:        {(self.topics_succeeded/max(1, self.topics_processed)*100):.1f}%")
        print(f"   Runtime:             {runtime:.1f}s")
        
        if self.durations:
            avg_duration = sum(self.durations) / len(self.durations)
            print(f"   Avg time/topic:      {avg_duration:.1f}s")
            print(f"   Topics/minute:       {(self.topics_processed / (runtime / 60)):.1f}")
        
        print(f"\n💰 COST")
        print(f"   Tokens used:         {cost_tracker.tokens_used:,}")
        print(f"   Today's spend:       ${cost_tracker.get_today_cost():.4f}")
        
        if cost_tracker.costs_by_provider:
            print(f"\n   By provider:")
            for provider, cost in cost_tracker.costs_by_provider.items():
                pct = (cost / cost_tracker.get_today_cost() * 100) if cost_tracker.get_today_cost() > 0 else 0
                print(f"      {provider:12s}  ${cost:.4f} ({pct:.1f}%)")
        
        if self.by_category:
            print(f"\n📁 BY CATEGORY")
            for category, stats in sorted(self.by_category.items()):
                total = stats['success'] + stats['failed']
                success_rate = (stats['success'] / total * 100) if total > 0 else 0
                print(f"   {category:12s}  {stats['success']}/{total} ({success_rate:.0f}%)")
        
        print("\n" + "="*80 + "\n")


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
    
    print(f"\n⚙️  CONFIGURATION")
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
    
    async def process_one_topic(topic, db):
        """Process a single topic with tracking."""
        async with semaphore:
            category = topic.category or "unknown"
            start = time.time()
            
            try:
                logger.info(f"▶️  Processing [{category}] {topic.title[:50]}...")
                
                job = GenerateTopicAnalysisJob(db, rate_limiter, cost_tracker)
                await job.execute(topic.id)
                
                duration = time.time() - start
                monitor.record_success(category, duration)
                logger.info(f"✅ Completed in {duration:.1f}s")
                
            except Exception as e:
                monitor.record_failure(category)
                logger.error(f"❌ Failed: {str(e)[:100]}")
    
    async with AsyncSessionLocal() as db:
        # Fetch pending topics
        query = select(Topic).outerjoin(TopicAnalysis).where(
            TopicAnalysis.id == None,
            Topic.category != None,
            or_(Topic.status != 'analysis_failed', Topic.status == None),
            or_(Topic.overall_sentiment != 'error', Topic.overall_sentiment == None)
        ).limit(BATCH_SIZE)
        
        result = await db.execute(query)
        topics = result.scalars().all()
        
        if not topics:
            print("ℹ️  No pending topics to process")
            return
        
        print(f"📋 Found {len(topics)} topics to process")
        
        # Group by category if enabled
        if BATCH_BY_CATEGORY:
            by_category = defaultdict(list)
            for topic in topics:
                by_category[topic.category or "unknown"].append(topic)
            
            print(f"\n📦 BATCHING BY CATEGORY")
            for cat, cat_topics in sorted(by_category.items()):
                print(f"   {cat:12s}  {len(cat_topics)} topics")
            print()
            
            # Process category by category
            for category, cat_topics in sorted(by_category.items()):
                print(f"\n🔄 Processing {category} category ({len(cat_topics)} topics)...")
                
                # Check budget before each category
                if not cost_tracker.can_process(DAILY_BUDGET):
                    print(f"⚠️  Daily budget reached (${cost_tracker.get_today_cost():.2f} / ${DAILY_BUDGET:.2f})")
                    print(f"   Stopping pipeline")
                    break
                
                # Process topics in parallel within category
                tasks = [process_one_topic(t, db) for t in cat_topics]
                await asyncio.gather(*tasks)
                
                print(f"✅ {category} category complete")
        
        else:
            # Process all topics in parallel (no grouping)
            print(f"\n🔄 Processing all topics in parallel...")
            
            tasks = []
            for topic in topics:
                # Check budget before each topic
                if not cost_tracker.can_process(DAILY_BUDGET):
                    print(f"⚠️  Daily budget reached (${cost_tracker.get_today_cost():.2f} / ${DAILY_BUDGET:.2f})")
                    break
                
                tasks.append(process_one_topic(topic, db))
            
            await asyncio.gather(*tasks)
    
    # Print final summary
    monitor.print_summary(cost_tracker)
    
    print("[OK] AI analysis step complete")


async def main():
    """Main pipeline orchestrator."""
    
    # You can uncomment other steps if needed
    # await step1_fetch()
    # await step2_normalize()
    # await step3_cluster()
    
    await step4_ai_analysis()
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETE".center(80))
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
