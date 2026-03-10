"""
run_cluster_and_analyze.py
Step 1: Cluster all newly-embedded unstopped articles into topics.
Step 2: Run Claude AI analysis on all topics that lack analysis.
"""
import asyncio
import os
import sys
import logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress overly verbose SQLAlchemy output
logging.basicConfig(level=logging.WARNING)

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ArticleEmbedding, RawArticle, TopicArticle, Topic, TopicAnalysis
from app.services.ai.clustering_service import ClusteringService
from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob

SEP = "=" * 60

async def step1_cluster():
    print("\n" + SEP)
    print("  STEP 1: CLUSTERING NEW ARTICLES")
    print(SEP)
    async with AsyncSessionLocal() as db:
        query = (
            select(ArticleEmbedding, RawArticle.title, RawArticle.category)
            .join(RawArticle, RawArticle.id == ArticleEmbedding.article_id)
            .outerjoin(TopicArticle, TopicArticle.article_id == ArticleEmbedding.article_id)
            .where(TopicArticle.topic_id == None)
        )
        result = await db.execute(query)
        items = result.all()
        print(f"  Unclustered embedded articles: {len(items)}")

        if not items:
            print("  Nothing to cluster. [OK]")
            return 0

        cluster_svc = ClusteringService(db)
        assigned = 0
        for emb_record, title, category in items:
            try:
                topic_id = await cluster_svc.find_or_create_topic(emb_record.embedding, title)
                await cluster_svc.assign_article_to_topic(emb_record.article_id, topic_id)

                # Propagate category to topic
                if category:
                    t_res = await db.execute(select(Topic).where(Topic.id == topic_id))
                    topic_obj = t_res.scalar_one_or_none()
                    if topic_obj and not topic_obj.category:
                        topic_obj.category = category
                assigned += 1
            except Exception as e:
                print(f"    [WARN] Clustering error for article {emb_record.article_id}: {str(e)[:80]}")

        await db.commit()

        # Report
        r = await db.execute(select(Topic))
        topics = r.scalars().all()
        with_cat = [t for t in topics if t.category]
        print(f"  Assigned: {assigned} articles to topics")
        print(f"  Total topics: {len(topics)} | With category: {len(with_cat)}")
        return len(topics)


async def step2_analyze(limit=50):
    print("\n" + SEP)
    print("  STEP 2: CLAUDE AI ANALYSIS")
    print(SEP)
    async with AsyncSessionLocal() as db:
        # Get all topics without existing analysis
        query = (
            select(Topic.id, Topic.title, Topic.category)
            .outerjoin(TopicAnalysis, TopicAnalysis.topic_id == Topic.id)
            .where(TopicAnalysis.id == None)
            .where(Topic.category != None)
            .limit(limit)
        )
        result = await db.execute(query)
        pending = result.all()
        print(f"  Topics needing analysis: {len(pending)} (limit={limit})")

        if not pending:
            print("  All topics already have analysis! [OK]")
            return 0

        success = 0
        fail = 0
        for i, (topic_id, title, category) in enumerate(pending, 1):
            print(f"  [{i}/{len(pending)}] [{category}] {(title or '')[:60]}...")
            try:
                async with AsyncSessionLocal() as job_db:
                    job = GenerateTopicAnalysisJob(job_db)
                    await job.execute(topic_id)
                success += 1
                print(f"    -> [OK] Analysis generated")
            except Exception as e:
                fail += 1
                err = str(e)[:100]
                print(f"    -> [FAIL] {err}")

        print(f"\n  Analysis complete: {success} succeeded, {fail} failed")
        return success


async def main():
    topic_count = await step1_cluster()
    analyzed = await step2_analyze(limit=50)

    print("\n" + SEP)
    print("  PIPELINE COMPLETE")
    print(SEP)
    print(f"  Total topics: {topic_count}")
    print(f"  Topics analyzed this run: {analyzed}")
    print(SEP + "\n")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
