import asyncio
from typing import Optional
from celery import shared_task
from app.database import AsyncSessionLocal, engine
from app.utils.jobs import create_job_record, update_job_status
from app.constants import DEFAULT_CATEGORY
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
import sys

def run_async(coro):
    """Run an async coroutine synchronously in a fresh event loop.
    Uses new_event_loop() to avoid deprecation warnings in Python 3.10+
    and to prevent event loop conflicts inside Celery workers.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            # Attempt to close pending tasks to avoid loop leak warnings
            if hasattr(asyncio, "all_tasks"):
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except:
            pass
        loop.close()
        asyncio.set_event_loop(None)

async def check_feature_flag(db, key: str) -> bool:
    from app.models.settings import FeatureFlag
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = result.scalar_one_or_none()
    return flag.enabled if flag else True

async def update_source_health(db, source_id: int, success: bool):
    from app.models.source import SourceHealth
    from datetime import datetime
    result = await db.execute(select(SourceHealth).where(SourceHealth.source_id == source_id))
    health = result.scalar_one_or_none()
    if not health:
        health = SourceHealth(source_id=source_id)
        db.add(health)
    if success:
        health.status = "healthy"
        health.last_success = datetime.now()
        health.fail_count = 0
    else:
        # Avoid AttributeError if fail_count is None
        if health.fail_count is None:
            health.fail_count = 0
        health.fail_count += 1
        health.status = "down" if health.fail_count > 5 else "degraded" if health.fail_count > 2 else "healthy"
    await db.commit()

@shared_task(name="fetch_articles_job", bind=True, max_retries=3, default_retry_delay=300)
def fetch_articles_job(self, job_id: str = None):
    """Job to fetch raw articles from external sources."""
    
    async def _run():
        jid = job_id
        try:
            async with AsyncSessionLocal() as db:
                if not jid:
                     # Fallback if triggered without ID (e.g. cron)
                     jid = await create_job_record(db, "FETCH_ARTICLES")

                await update_job_status(db, jid, "RUNNING")
                
                if not await check_feature_flag(db, "CRAWLER"):
                    logger.info("Crawler feature flag is disabled.")
                    await update_job_status(db, jid, "COMPLETED", result={"status": "skipped", "reason": "feature_disabled"})
                    return 0
                
                # Fetch sources and process them
                from app.models.source import Source
                from app.services.crawler_service import CrawlerService
                
                crawler = CrawlerService(db)
                res = await db.execute(select(Source).where(Source.is_active == True))
                sources = res.scalars().all()
                
                total_fetched = 0
                results_summary = []
                
                for s in sources:
                    try:
                        logger.info(f"Fetching from source: {s.name}")
                        count = await crawler.fetch_articles(s)
                        total_fetched += count
                        await update_source_health(db, s.id, success=True)
                        results_summary.append({"source": s.name, "status": "success", "count": count})
                    except Exception as e:
                        logger.error(f"Error fetching from {s.name}: {e}")
                        await update_source_health(db, s.id, success=False)
                        results_summary.append({"source": s.name, "status": "failed", "error": str(e)})

                # Determine final job status
                all_failed = all(r["status"] == "failed" for r in results_summary)
                
                if all_failed and sources:
                    await update_job_status(db, jid, "FAILED", error="All sources failed to fetch.", result={"details": results_summary})
                else:
                    await update_job_status(db, jid, "COMPLETED", result={"fetched_count": total_fetched, "sources_count": len(sources), "details": results_summary})
                
                return len(sources) if sources else 0
        except Exception as e:
            logger.error(f"Error in fetch_articles_job inner: {e}")
            if jid:
                 async with AsyncSessionLocal() as db:
                    await update_job_status(db, jid, "FAILED", error=str(e))
            raise e
        finally:
            try:
                await engine.dispose()
            except:
                pass
    
    try:
        count = run_async(_run())
        if count and count > 0:
            try:
                normalize_articles_job.delay(job_id=None)
            except Exception as chain_err:
                logger.warning(f"Could not chain normalize after fetch: {chain_err}")
        return {"status": "success", "job_id": job_id}
    except Exception as exc:
        raise self.retry(exc=exc)

@shared_task(name="normalize_articles_job", bind=True, max_retries=3)
def normalize_articles_job(self, job_id: str = None):
    """Job to clean and structure raw articles, extract entities and generate embeddings."""
    from app.services.ai.nlp_service import NLPService
    from app.services.ai.embedding_service import EmbeddingService
    from app.models import ArticleEntity, ArticleEmbedding, RawArticle
    
    async def _run():
        jid = job_id
        try:
            async with AsyncSessionLocal() as db:
                if not jid:
                     jid = await create_job_record(db, "NORMALIZE_ARTICLES")
                
                await update_job_status(db, jid, "RUNNING")
                
                if not await check_feature_flag(db, "AI_NORMALIZATION"):
                    logger.info("AI Normalization feature flag is disabled.")
                    await update_job_status(db, jid, "COMPLETED", result={"status": "skipped"})
                    return 0
                
                nlp = NLPService()
                embedder = EmbeddingService()
                
                query = select(RawArticle).where(RawArticle.sentiment_score == None).limit(50)
                result = await db.execute(query)
                articles = result.scalars().all()
                
                for article in articles:
                    entities = nlp.extract_entities(article.title + " " + (article.description or ""))
                    for ent in entities:
                        ae = ArticleEntity(article_id=article.id, entity_name=ent["text"], entity_type=ent["label"])
                        db.add(ae)
                    
                    vec = embedder.generate_embedding(article.title)
                    emb = ArticleEmbedding(article_id=article.id, embedding=vec)
                    db.add(emb)
                    
                    article.sentiment_score = 0.0 

                    if not article.category:
                        text_content = (article.title + " " + (article.content or "")).lower()
                        if any(x in text_content for x in ["senate", "president", "election", "law", "policy", "government", "minister", "tinubu", "governor", "apc", "pdp", "lp", "national assembly"]):
                            article.category = "politics"
                        elif any(x in text_content for x in ["naira", "inflation", "gdp", "cbn", "fiscal", "monetary", "currency", "forex", "interest rate", "budget", "poverty", "debt"]):
                            article.category = "economy"
                        elif any(x in text_content for x in ["market", "bank", "stock", "trade", "refinery", "dangote", "startup", "entrepreneur", "company", "merger", "acquisition", "investment", "profit", "revenue"]):
                            article.category = "business"
                        elif any(x in text_content for x in ["football", "afcon", "match", "league", "sport", "super eagles", "npfl", "olympics", "fifa", "caf", "stadium", "athlete", "tournament"]):
                            article.category = "sport"
                        elif any(x in text_content for x in ["ai", "software", "digital", "cyber", "crypto", "tech", "fintech", "blockchain", "innovation", "semiconductor", "gadget", "smartphone", "silicon"]):
                            article.category = "technology"
                        elif any(x in text_content for x in ["police", "army", "attack", "kidnap", "bandit", "terror", "insurgent", "robbery", "piracy", "security", "military", "insecurity", "efcc"]):
                            article.category = "security"
                        elif any(x in text_content for x in ["ecowas", "west africa", "cross-border", "bilateral", "diplomatic", "embassy", "foreign affairs"]):
                            article.category = "regional"
                        elif any(x in text_content for x in ["climate", "pollution", "deforestation", "niger delta", "oil spill", "conservation", "environment", "global warming", "carbon"]):
                            article.category = "environment"
                        elif any(x in text_content for x in ["health", "education", "poverty", "community", "welfare", "gender", "youth", "women", "university", "hosptial", "doctor"]):
                            article.category = "social"
                        elif any(x in text_content for x in ["global impact", "international", "united nations", "un", "world bank", "imf", "treaty", "foreign aid"]):
                            article.category = "global-impact"
                        else:
                            article.category = DEFAULT_CATEGORY
                    
                await db.commit()
                await update_job_status(db, jid, "COMPLETED", result={"normalized_count": len(articles)})
                return len(articles)
        except Exception as e:
            logger.error(f"Error in normalize_articles_job: {e}")
            if jid:
                 async with AsyncSessionLocal() as db:
                    await update_job_status(db, jid, "FAILED", error=str(e))
            raise e
        finally:
            try:
                await engine.dispose()
            except:
                pass

    try:
        count = run_async(_run())
        if count and count > 0:
            try:
                clustering_job.delay(job_id=None)
            except Exception as chain_err:
                logger.warning(f"Could not chain clustering after normalize: {chain_err}")
        return {"status": "completed", "normalized_count": count}
    except Exception as exc:
        raise self.retry(exc=exc)

@shared_task(name="clustering_job", bind=True, max_retries=3)
def clustering_job(self, job_id: str = None):
    """Job to group articles into topics using vector similarity."""
    from app.services.ai.clustering_service import ClusteringService
    from app.models import ArticleEmbedding, RawArticle, TopicArticle
    
    async def _run():
        jid = job_id
        try:
            async with AsyncSessionLocal() as db:
                if not jid:
                     jid = await create_job_record(db, "CLUSTERING")
                
                await update_job_status(db, jid, "RUNNING")
                cluster_svc = ClusteringService(db)
                
                query = (
                    select(ArticleEmbedding, RawArticle.title)
                    .join(RawArticle, RawArticle.id == ArticleEmbedding.article_id)
                    .outerjoin(TopicArticle, TopicArticle.article_id == ArticleEmbedding.article_id)
                    .where(TopicArticle.topic_id == None)
                    .limit(50)
                )
                result = await db.execute(query)
                items = result.all()
                
                for emb_record, title in items:
                    topic_id = await cluster_svc.find_or_create_topic(emb_record.embedding, title)
                    await cluster_svc.assign_article_to_topic(emb_record.article_id, topic_id)
                    
                    article_res = await db.execute(select(RawArticle).where(RawArticle.id == emb_record.article_id))
                    article = article_res.scalar_one_or_none()
                    if article and article.category:
                        from app.models import Topic
                        topic_res = await db.execute(select(Topic).where(Topic.id == topic_id))
                        topic_obj = topic_res.scalar_one_or_none()
                        if topic_obj and not topic_obj.category:
                            topic_obj.category = article.category.lower()
                
                await update_job_status(db, jid, "COMPLETED", result={"clustered_count": len(items)})
                return len(items)
        except Exception as e:
            logger.error(f"Error in clustering_job: {e}")
            if jid:
                 async with AsyncSessionLocal() as db:
                    await update_job_status(db, jid, "FAILED", error=str(e))
            raise e
        finally:
            try:
                await engine.dispose()
            except:
                pass

    try:
        count = run_async(_run())
        try:
            ai_analysis_job.delay(job_id=None)
        except Exception as chain_err:
            logger.warning(f"Could not chain AI analysis after clustering: {chain_err}")
        return {"status": "completed", "clustered_count": count}
    except Exception as exc:
        raise self.retry(exc=exc)

@shared_task(name="ai_analysis_job", bind=True, max_retries=3)
def ai_analysis_job(self, job_id: str = None, topic_id: Optional[int] = None):
    """Job to generate comprehensive AI analysis for a topic using category-specific configurations."""
    async def _run():
        jid = job_id
        try:
            from app.jobs.generate_topic_analysis_job import GenerateTopicAnalysisJob
            from app.models import Topic, TopicAnalysis
            
            async with AsyncSessionLocal() as db:
                if not jid:
                     jid = await create_job_record(db, "AI_ANALYSIS", payload={"topic_id": topic_id})

                await update_job_status(db, jid, "RUNNING")
                job = GenerateTopicAnalysisJob(db)

                if topic_id is not None:
                    await job.execute(topic_id)
                else:
                    query = select(Topic.id).outerjoin(TopicAnalysis).where(TopicAnalysis.id == None)
                    result = await db.execute(query)
                    topic_ids = result.scalars().all()
                    for t_id in topic_ids:
                        await job.execute(t_id)
                
                await update_job_status(db, jid, "COMPLETED")
                return "Analysis complete"
        except Exception as e:
            logger.error(f"Error in ai_analysis_job: {e}")
            if jid:
                 async with AsyncSessionLocal() as db:
                    await update_job_status(db, jid, "FAILED", error=str(e))
            raise e
        finally:
            try:
                await engine.dispose()
            except:
                pass

    try:
        result = run_async(_run())
        return {"status": "completed", "result": result}
    except Exception as exc:
        raise self.retry(exc=exc)

@shared_task(name="trend_update_job", bind=True, max_retries=3)
def trend_update_job(self, job_id: str = None):
    """Job to update topic trending status based on recent activity."""
    from app.models import Topic, TopicTrend, RawArticle, TopicArticle
    from datetime import datetime, timedelta
    from sqlalchemy import func

    async def _run():
        jid = job_id
        try:
            async with AsyncSessionLocal() as db:
                if not jid:
                    jid = await create_job_record(db, "TREND_UPDATE")
                
                await update_job_status(db, jid, "RUNNING")
                since = datetime.now() - timedelta(hours=24)
                
                query = (
                    select(
                        Topic.id, 
                        func.count(RawArticle.id).label("article_count"),
                        func.count(func.distinct(RawArticle.source_id)).label("source_count")
                    )
                    .join(TopicArticle, Topic.id == TopicArticle.topic_id)
                    .join(RawArticle, TopicArticle.article_id == RawArticle.id)
                    .where(RawArticle.published_at >= str(since))
                    .group_by(Topic.id)
                )
                
                result = await db.execute(query)
                topic_stats = result.all()
                
                updated_count = 0
                for t_id, a_count, s_count in topic_stats:
                    score = (a_count * 1.0) + (s_count * 2.0)
                    trend = TopicTrend(topic_id=t_id, interest_score=score, date=datetime.now())
                    db.add(trend)
                    
                    is_trending = score > 10
                    t_query = select(Topic).where(Topic.id == t_id)
                    t_res = await db.execute(t_query)
                    topic = t_res.scalar_one()
                    topic.is_trending = is_trending
                    topic.confidence_score = min(1.0, score / 20.0)
                    updated_count += 1
                
                await db.commit()
                await update_job_status(db, jid, "COMPLETED", result={"topics_updated": updated_count})
                return f"Trends updated for {updated_count} topics"
        except Exception as e:
            logger.error(f"Error in trend_update_job: {e}")
            if jid:
                 async with AsyncSessionLocal() as db:
                     await update_job_status(db, jid, "FAILED", error=str(e))
            raise e
        finally:
            try:
                await engine.dispose()
            except:
                pass

    try:
        res = run_async(_run())
        return {"status": "completed", "result": res}
    except Exception as exc:
        raise self.retry(exc=exc)

@shared_task(bind=True, max_retries=3)
def video_fetch_job(self, job_id: str = None, topic_id: int = None):
    """Job to fetch related videos for a topic from YouTube."""
    from app.models import Topic, TopicVideo
    from app.config import settings
    import httpx
    
    async def _fetch_for_topic(db, t_id: int):
        res = await db.execute(select(Topic).where(Topic.id == t_id))
        topic = res.scalar_one_or_none()
        if not topic:
            return 0
            
        api_key = settings.YOUTUBE_API_KEY
        if not api_key:
            return 0
            
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": f"{topic.title} news",
            "type": "video",
            "maxResults": 3,
            "order": "date",
            "key": api_key,
            "relevanceLanguage": "en"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(search_url, params=params)
            
        if resp.status_code != 200:
            return 0
            
        data = resp.json()
        items = data.get("items", [])
        
        count = 0
        for item in items:
            vid_id = item["id"]["videoId"]
            snippet = item["snippet"]
            v_url = f"https://www.youtube.com/watch?v={vid_id}"
            exists = await db.execute(select(TopicVideo).where(TopicVideo.topic_id == t_id, TopicVideo.video_url == v_url))
            if exists.scalar_one_or_none():
                continue
                
            video = TopicVideo(
                topic_id=t_id,
                video_url=v_url,
                title=snippet["title"],
                thumbnail_url=snippet["thumbnails"]["high"]["url"],
                source_platform="youtube"
            )
            db.add(video)
            count += 1
            
        await db.commit()
        return count

    async def _run():
        jid = job_id
        try:
            async with AsyncSessionLocal() as db:
                if not jid:
                    jid = await create_job_record(db, "VIDEO_FETCH", payload={"topic_id": topic_id})
                
                await update_job_status(db, jid, "RUNNING")
                
                total_videos = 0
                if topic_id:
                    total_videos = await _fetch_for_topic(db, topic_id)
                else:
                    query = select(Topic).where(Topic.is_trending == True)
                    result = await db.execute(query)
                    topics = result.scalars().all()
                    for t in topics:
                        cnt = await _fetch_for_topic(db, t.id)
                        total_videos += cnt
                
                await update_job_status(db, jid, "COMPLETED", result={"videos_fetched": total_videos})
                return f"Fetched {total_videos} videos"
        except Exception as e:
             logger.error(f"Error in video_fetch_job: {e}")
             if jid:
                  async with AsyncSessionLocal() as db:
                      await update_job_status(db, jid, "FAILED", error=str(e))
             raise e
        finally:
            try:
                await engine.dispose()
            except:
                pass

    try:
        res = run_async(_run())
        return {"status": "completed", "result": res}
    except Exception as exc:
         raise self.retry(exc=exc)
