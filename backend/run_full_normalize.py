"""
run_full_normalize.py
Normalizes ALL unnormalized articles (no batch limit cap).
Strips HTML, generates embeddings, categorizes, then triggers
clustering + AI analysis for new topics.
"""
import asyncio
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ArticleEntity, ArticleEmbedding, RawArticle
from app.constants import DEFAULT_CATEGORY
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

BATCH_SIZE = 100

async def normalize_all():
    from app.services.ai.nlp_service import NLPService
    from app.services.ai.embedding_service import EmbeddingService

    nlp = NLPService()
    embedder = EmbeddingService()

    total_done = 0
    batch_num = 0

    while True:
        async with AsyncSessionLocal() as db:
            query = select(RawArticle).where(RawArticle.sentiment_score == None).limit(BATCH_SIZE)
            result = await db.execute(query)
            articles = result.scalars().all()

            if not articles:
                break

            batch_num += 1
            batch_total = len(articles)
            print(f"\n  Batch {batch_num}: processing {batch_total} articles...")

            processed = 0
            for article in articles:
                try:
                    # 1. Strip HTML
                    raw_text = (article.title or "") + " " + (article.content or "")
                    clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip().lower()

                    # 2. Entity extraction
                    entities = nlp.extract_entities(
                        article.title + " " + (article.description or "")
                    )
                    for ent in entities:
                        db.add(ArticleEntity(
                            article_id=article.id,
                            entity_name=ent["text"],
                            entity_type=ent["label"]
                        ))

                    # 3. Embedding on clean text
                    vec = embedder.generate_embedding(clean_text[:500])
                    db.add(ArticleEmbedding(article_id=article.id, embedding=vec))

                    # 4. Mark as processed
                    article.sentiment_score = 0.0

                    # 5. Category — canonical slugs from constants.py ONLY
                    if not article.category:
                        t = clean_text
                        if any(x in t for x in ["senate", "president", "election", "law", "policy",
                                                 "government", "minister", "tinubu", "governor"]):
                            article.category = "politics"
                        elif any(x in t for x in ["naira", "inflation", "gdp", "cbn", "fiscal",
                                                   "monetary", "currency", "forex", "interest rate", "budget"]):
                            article.category = "economy"
                        elif any(x in t for x in ["market", "bank", "stock", "trade", "refinery",
                                                   "dangote", "startup", "entrepreneur", "company", "business"]):
                            article.category = "business"
                        elif any(x in t for x in ["ai", "software", "digital", "cyber", "crypto",
                                                   "tech", "fintech", "blockchain", "satellite"]):
                            article.category = "technology"
                        elif any(x in t for x in ["football", "afcon", "match", "league", "sport",
                                                   "npfl", "super eagles"]):
                            article.category = "sports"
                        elif any(x in t for x in ["police", "army", "attack", "kidnap", "bandit",
                                                   "terror", "insurgent", "robbery", "piracy", "crime"]):
                            article.category = "security"
                        elif any(x in t for x in ["ecowas", "west africa", "cross-border",
                                                   "bilateral", "diplomatic", "foreign"]):
                            article.category = "regional"
                        elif any(x in t for x in ["climate", "pollution", "deforestation",
                                                   "niger delta", "oil spill", "conservation", "environment"]):
                            article.category = "environment"
                        elif any(x in t for x in ["health", "education", "poverty", "community",
                                                   "welfare", "gender", "youth", "women", "social"]):
                            article.category = "social"
                        else:
                            article.category = DEFAULT_CATEGORY

                    processed += 1

                except Exception as e:
                    print(f"    [WARN] Article {article.id} error: {e}")

            await db.commit()
            total_done += processed
            print(f"  Batch {batch_num} done: {processed}/{batch_total} normalized. Total so far: {total_done}")

    print(f"\n  All done! Total normalized: {total_done} articles.\n")
    return total_done

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("\n" + "=" * 60)
    print("  FULL NORMALIZATION RUN")
    print("=" * 60)
    asyncio.run(normalize_all())
    print("=" * 60 + "\n")
