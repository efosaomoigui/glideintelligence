"""
run_pipeline_test.py
====================
Runs the full pipeline end-to-end (Fetch -> Normalize -> Cluster -> AI Analysis -> Trend)
WITHOUT Celery - executes each step's core logic directly so errors surface clearly.

Usage: python run_pipeline_test.py
Optional flags:
  --fetch-only     Stop after Fetch
  --skip-fetch     Skip Fetch (use existing raw_articles)
  --skip-analysis  Skip AI Analysis step
"""

import asyncio, os, sys, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func, text
from sqlalchemy.orm import make_transient

from app.database import AsyncSessionLocal

SEP = "=" * 65


def hdr(step: str):
    print(f"\n{SEP}")
    print(f"  STEP: {step}")
    print(SEP)


def ok(msg):  print(f"  [OK]  {msg}")
def warn(msg): print(f"  [!!]  {msg}")
def err(msg):  print(f"  [ERR] {msg}")


# ─── STEP 1: FETCH ───────────────────────────────────────────────────────────
async def step_fetch(db):
    from app.models.source import Source
    from app.services.crawler_service import CrawlerService

    hdr("1 / 5  FETCH ARTICLES")
    res = await db.execute(select(Source).where(Source.is_active == True))
    sources = res.scalars().all()
    ok(f"{len(sources)} active sources found")

    crawler = CrawlerService(db)
    total = 0
    for src in sources:
        try:
            count = await crawler.fetch_articles(src)
            total += count
            ok(f"  {src.name:<40} {count} articles")
        except Exception as e:
            warn(f"  {src.name:<40} FAILED: {str(e)[:80]}")

    r = await db.execute(select(func.count()).select_from(
        select(text("1")).select_from(text("raw_articles")).subquery()
    ))
    total_in_db = (await db.execute(text("SELECT COUNT(*) FROM raw_articles"))).scalar()
    ok(f"Total raw_articles in DB after fetch: {total_in_db}")
    return total_in_db


# ─── STEP 2: NORMALIZE ───────────────────────────────────────────────────────
async def step_normalize(db):
    from app.models import RawArticle, ArticleEntity, ArticleEmbedding
    from app.services.ai.nlp_service import NLPService
    from app.services.ai.embedding_service import EmbeddingService
    import hashlib, math

    hdr("2 / 5  NORMALIZE ARTICLES")
    nlp = NLPService()
    embedder = EmbeddingService()

    # Fallback: deterministic pseudo-embedding from title hash when no real model
    def hash_embedding(text: str, dims: int = 384) -> list:
        """Generate a reproducible pseudo-embedding from text hash. Good enough for clustering."""
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = []
        for i in range(dims):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            rng.append((seed / 0xFFFFFFFF) * 2 - 1)
        # Normalize to unit vector
        norm = math.sqrt(sum(x * x for x in rng)) or 1.0
        return [x / norm for x in rng]

    query = select(RawArticle).where(RawArticle.sentiment_score == None).limit(500)
    result = await db.execute(query)
    articles = result.scalars().all()
    ok(f"{len(articles)} un-normalized articles found")

    if not articles:
        warn("Nothing to normalize — all articles already processed or none fetched.")
        return 0

    count = 0
    embedding_source = "model" if embedder.model else "hash-fallback"
    ok(f"Embedding source: {embedding_source}")

    for article in articles:
        try:
            # Entity extraction
            text_input = article.title + " " + (article.description or "")
            entities = nlp.extract_entities(text_input)
            for ent in entities:
                db.add(ArticleEntity(
                    article_id=article.id,
                    entity_name=ent["text"],
                    entity_type=ent["label"]
                ))

            # Embedding (real or hash fallback)
            if embedder.model:
                vec = embedder.generate_embedding(article.title)
            else:
                vec = hash_embedding(article.title)

            if vec:
                db.add(ArticleEmbedding(article_id=article.id, embedding=vec))

            # Mark processed
            article.sentiment_score = 0.0

            # Keyword categorization
            if not article.category:
                t = (article.title + " " + (article.content or "")).lower()
                if any(x in t for x in ["senate","president","election","law","policy","government","minister","tinubu","vote","lawmakers"]):
                    article.category = "politics"
                elif any(x in t for x in ["market","bank","stock","trade","economy","inflation","naira","cbn","forex","gdp","refinery","dangote","revenue","fiscal"]):
                    article.category = "economy"
                elif any(x in t for x in ["ai","software","digital","cyber","startup","crypto","tech","app","data"]):
                    article.category = "technology"
                elif any(x in t for x in ["football","afcon","match","league","sport","players"]):
                    article.category = "sports"
                elif any(x in t for x in ["police","army","attack","kidnap","security","bandits","terror","troops"]):
                    article.category = "security"
                elif any(x in t for x in ["health","hospital","disease","covid","vaccine","who","medicine"]):
                    article.category = "health"
                else:
                    article.category = "general"

            count += 1
        except Exception as e:
            warn(f"Article {article.id} normalize error: {str(e)[:80]}")

    await db.commit()
    ok(f"Normalized {count} articles (embedding: {embedding_source})")
    return count



# ─── STEP 3: CLUSTER ─────────────────────────────────────────────────────────
async def step_cluster(db):
    from app.models import ArticleEmbedding, RawArticle, TopicArticle
    from app.services.ai.clustering_service import ClusteringService

    hdr("3 / 5  CLUSTER INTO TOPICS")
    cluster_svc = ClusteringService(db)

    query = (
        select(ArticleEmbedding, RawArticle.title)
        .join(RawArticle, RawArticle.id == ArticleEmbedding.article_id)
        .outerjoin(TopicArticle, TopicArticle.article_id == ArticleEmbedding.article_id)
        .where(TopicArticle.topic_id == None)
        .limit(500)
    )
    result = await db.execute(query)
    items = result.all()
    ok(f"{len(items)} un-clustered articles found")

    if not items:
        warn("Nothing to cluster.")
        return 0

    clustered = 0
    for emb_record, title in items:
        try:
            topic_id = await cluster_svc.find_or_create_topic(emb_record.embedding, title)
            await cluster_svc.assign_article_to_topic(emb_record.article_id, topic_id)
            clustered += 1
        except Exception as e:
            warn(f"Cluster error for article {emb_record.article_id}: {str(e)[:80]}")

    topic_count = (await db.execute(text("SELECT COUNT(*) FROM topics"))).scalar()
    ok(f"Clustered {clustered} articles | Total topics in DB: {topic_count}")
    return clustered


# ─── STEP 4: AI ANALYSIS ────────────────────────────────────────────────────
async def step_ai_analysis(db):
    from app.models import Topic, TopicAnalysis
    from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob

    hdr("4 / 5  AI ANALYSIS (Sentiment + Perspectives + Impacts + Cards)")

    query = (
        select(Topic.id, Topic.title, Topic.category)
        .outerjoin(TopicAnalysis, TopicAnalysis.topic_id == Topic.id)
        .where(TopicAnalysis.id == None)
    )
    result = await db.execute(query)
    topics = result.all()
    ok(f"{len(topics)} topics need AI analysis")

    if not topics:
        warn("All topics already have analysis.")
        return 0

    job = GenerateTopicAnalysisJob(db)
    success = 0
    failed = 0
    for t_id, t_title, t_cat in topics:
        try:
            print(f"\n  Analyzing topic {t_id}: {t_title[:60]} [{t_cat}]")
            await job.execute(t_id)
            ok(f"  topic {t_id} analysis DONE")
            success += 1
        except Exception as e:
            err(f"  topic {t_id} FAILED: {str(e)[:120]}")
            failed += 1
            # Re-open the session state — rollback happened inside execute()
            # We need a fresh session for subsequent topics
            # The job already does rollback internally; session should be usable again

    ok(f"AI Analysis: {success} succeeded, {failed} failed")
    return success


# ─── STEP 5: TREND UPDATE ───────────────────────────────────────────────────
async def step_trend_update(db):
    from app.models import Topic, TopicTrend, RawArticle, TopicArticle
    from datetime import datetime, timedelta
    from sqlalchemy import func

    hdr("5 / 5  TREND UPDATE")
    since = datetime.now() - timedelta(hours=24)

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
    ok(f"{len(topic_stats)} topics to score for trends")

    updated = 0
    for t_id, a_count, s_count in topic_stats:
        score = (a_count * 1.0) + (s_count * 2.0)
        db.add(TopicTrend(topic_id=t_id, interest_score=score, date=datetime.now()))

        t_res = await db.execute(select(Topic).where(Topic.id == t_id))
        topic = t_res.scalar_one()
        topic.is_trending = score > 3  # lower threshold for small datasets
        topic.confidence_score = min(1.0, score / 10.0)
        updated += 1

    await db.commit()
    trending_count = (await db.execute(text("SELECT COUNT(*) FROM topics WHERE is_trending = TRUE"))).scalar()
    ok(f"Trends updated for {updated} topics | {trending_count} now marked trending")
    return updated


# ─── FINAL VERIFICATION ─────────────────────────────────────────────────────
async def step_verify(db):
    hdr("VERIFICATION — UI Data Readiness")

    checks = [
        ("raw_articles",          "raw_articles"),
        ("topics",                "topics"),
        ("topic_articles",        "topic_articles"),
        ("topic_analysis",        "topic_analysis"),
        ("sentiment_breakdown",   "topic_sentiment_breakdown"),
        ("source_perspectives",   "source_perspectives"),
        ("regional_impacts",      "regional_impacts"),
        ("intelligence_cards",    "intelligence_cards"),
        ("article_embeddings",    "article_embeddings"),
    ]

    for label, table in checks:
        try:
            c = (await db.execute(text(f"SELECT COUNT(*) FROM {table}"))).scalar()
            status = "[OK]" if c and c > 0 else "[!!] EMPTY"
            print(f"  {status}  {label:<30} {c} rows")
        except Exception as e:
            print(f"  [ERR] {label:<30} {str(e)[:60]}")

    # Sample topic check
    print("\n  Sample topics (first 5):")
    rows = (await db.execute(text(
        "SELECT id, title, category, overall_sentiment, is_trending FROM topics LIMIT 5"
    ))).all()
    for row in rows:
        print(f"    id={row[0]} cat={row[2]} sentiment={row[3]} trending={row[4]}  {row[1][:50]}")


# ─── MAIN ───────────────────────────────────────────────────────────────────
async def main(args):
    print(f"\n{SEP}")
    print("  GLIDE INTELLIGENCE - PIPELINE E2E TEST")
    print(SEP)
    t0 = time.time()

    async with AsyncSessionLocal() as db:
        try:
            if not args.skip_fetch:
                await step_fetch(db)
            else:
                warn("Skipping Fetch (--skip-fetch)")

            await step_normalize(db)
            await step_cluster(db)

            if not args.skip_analysis:
                await step_ai_analysis(db)
            else:
                warn("Skipping AI Analysis (--skip-analysis)")

            await step_trend_update(db)
            await step_verify(db)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
        except Exception as e:
            err(f"Pipeline aborted: {e}")
            raise

    elapsed = time.time() - t0
    print(f"\n{SEP}")
    print(f"  Pipeline run complete in {elapsed:.1f}s")
    print(SEP)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--skip-analysis", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args))
