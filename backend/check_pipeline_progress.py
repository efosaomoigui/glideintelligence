import asyncio
import os
import sys
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.topic import Topic, TopicAnalysis, TopicArticle
from app.models.article import RawArticle
from app.models.intelligence import IntelligenceCard
from app.models.job import Job

async def check_counts():
    async with AsyncSessionLocal() as db:
        # Check articles
        res = await db.execute(select(func.count(RawArticle.id)))
        articles = res.scalar()
        
        # Check topics
        res = await db.execute(select(func.count(Topic.id)))
        topics = res.scalar()
        
        # Check associations
        res = await db.execute(select(func.count(TopicArticle.id)))
        assocs = res.scalar()
        
        # Check analysis
        res = await db.execute(select(func.count(TopicAnalysis.id)))
        analysis = res.scalar()
        
        # Check cards
        res = await db.execute(select(func.count(IntelligenceCard.id)))
        cards = res.scalar()
        
        # Check recent jobs
        res = await db.execute(select(Job).order_by(Job.created_at.desc()).limit(5))
        jobs = res.scalars().all()
        
        print("-" * 30)
        print(f"PIPELINE STATUS REPORT")
        print("-" * 30)
        print(f"Raw Articles:      {articles}")
        print(f"Topics:            {topics}")
        print(f"Article-Topic Maps: {assocs}")
        print(f"Topic Analysis:    {analysis}")
        print(f"Intelligence Cards: {cards}")
        print("-" * 30)
        print("RECENT JOBS:")
        for j in jobs:
            print(f"[{j.type}] {j.status} (ID: {j.id[:8]}...) Created: {j.created_at.strftime('%H:%M:%S') if j.created_at else 'Unknown'}")
        print("-" * 30)

if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    asyncio.run(check_counts())
