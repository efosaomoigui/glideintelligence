import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import TopicAnalysis, AISummary, RawArticle, Topic

async def check_results():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        article_count = (await session.execute(select(func.count(RawArticle.id)))).scalar()
        topic_count = (await session.execute(select(func.count(Topic.id)))).scalar()
        analysis_count = (await session.execute(select(func.count(TopicAnalysis.id)))).scalar()
        summary_count = (await session.execute(select(func.count(AISummary.id)))).scalar()
        
        print(f"Articles: {article_count}")
        print(f"Topics: {topic_count}")
        print(f"Topic Analyses: {analysis_count}")
        print(f"AI Summaries: {summary_count}")
        
    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_results())
