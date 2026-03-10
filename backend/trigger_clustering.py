import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.ai.clustering_service import ClusteringService
from app.models import ArticleEmbedding, RawArticle, TopicArticle
from sqlalchemy import select

async def trigger_clustering():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Initializing ClusteringService...")
        cluster_svc = ClusteringService(session)
        
        # Find articles with embeddings but no topic
        query = (
            select(ArticleEmbedding, RawArticle.title)
            .join(RawArticle, RawArticle.id == ArticleEmbedding.article_id)
            .outerjoin(TopicArticle, TopicArticle.article_id == ArticleEmbedding.article_id)
            .where(TopicArticle.topic_id == None)
            .limit(50)
        )
        result = await session.execute(query)
        items = result.all()
        
        print(f"Found {len(items)} articles to cluster.")
        
        for emb_record, title in items:
            safe_title = title.encode('ascii', 'ignore').decode('ascii')
            print(f"Processing: {safe_title[:30]}...")
            try:
                topic_id = await cluster_svc.find_or_create_topic(emb_record.embedding, title)
                await cluster_svc.assign_article_to_topic(emb_record.article_id, topic_id)
                print(f" -> Assigned to Topic ID: {topic_id}")
            except Exception as e:
                print(f"Error clustering article {emb_record.article_id}: {e}")
                import traceback
                traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(trigger_clustering())
