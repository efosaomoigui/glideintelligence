import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal
from app.models import Topic, TopicAnalysis, RawArticle, TopicArticle, Source
from sqlalchemy import select

async def seed_hero_data():
    print("Seeding Hero Section data...")
    async with AsyncSessionLocal() as db:
        # 1. Ensure Source exists
        source_name = "Guardian Nigeria"
        # Case insensitive lookup
        stmt = select(Source).where(Source.name.ilike(source_name))
        source = (await db.execute(stmt)).scalars().first()
        
        if not source:
            print(f"Creating source: {source_name}")
            source = Source(
                name=source_name, 
                url="https://guardian.ng", 
                reliability_score=0.9
            )
            db.add(source)
            try:
                await db.flush()
            except Exception as e:
                print(f"Error creating source: {e}")
                await db.rollback()
                stmt = select(Source).where(Source.name.ilike(source_name))
                source = (await db.execute(stmt)).scalars().first()
        
        if not source:
             print("Source creation failed and could not be found. Fetching ANY source.")
             stmt = select(Source).limit(1)
             source = (await db.execute(stmt)).scalars().first()
             
        if not source:
             print("CRITICAL: No sources exist in DB. Please run seed_sources.py first or ensure DB isn't empty.")
             return


        
        # 2. Create Topic "Minimum Wage Agreement"
        topic_title = "Minimum Wage Agreement"
        stmt = select(Topic).where(Topic.title == topic_title)
        topic = (await db.execute(stmt)).scalar_one_or_none()
        
        if not topic:
            topic = Topic(
                title=topic_title,
                description="Federal Government and organized labor reach consensus on new national minimum wage.",
                is_trending=True,
                status="developing",
                importance_score=0.95,
                source_count=12,
                comment_count=847,
                slug="minimum-wage-agreement",
                updated_at=datetime.utcnow()
            )
            db.add(topic)
            await db.flush()
            print(f"Created topic: {topic.title}")
        else:
            # Update existing to match current needs
            topic.is_trending = True
            topic.source_count = 12
            topic.comment_count = 847
            topic.updated_at = datetime.utcnow()
            print(f"Updated topic: {topic.title}")

        # 3. Create Topic Analysis (Summary & Bullets)
        stmt = select(TopicAnalysis).where(TopicAnalysis.topic_id == topic.id)
        analysis = (await db.execute(stmt)).scalar_one_or_none()
        
        summary_text = "After six months of negotiations, the Federal Government and labor unions have reached a tentative agreement on a new ₦70,000 minimum wage. The deal includes staggered implementation over 18 months."
        facts = [
            "Agreement covers 4.2 million federal workers",
            "Implementation begins July 2026",
            "Business groups warn of inflation pressure",
            "State governors request revenue sharing adjustments"
        ]
        
        if not analysis:
            analysis = TopicAnalysis(
                topic_id=topic.id,
                summary=summary_text,
                facts=facts,
                regional_framing={}
            )
            db.add(analysis)
            print("Created analysis")
        else:
            analysis.summary = summary_text
            analysis.facts = facts
            print("Updated analysis")

        # 4. Ensure at least one article exists for this topic (Hero Article)
        stmt = select(TopicArticle).where(TopicArticle.topic_id == topic.id)
        assoc = (await db.execute(stmt)).scalar_one_or_none()
        
        if not assoc:
            # Check if article exists first
            article_url = "https://guardian.ng/news/fg-labor-deal"
            stmt = select(RawArticle).where(RawArticle.url == article_url)
            article = (await db.execute(stmt)).scalar_one_or_none()
            
            if not article:
                # Create article
                article = RawArticle(
                    source_id=source.id,
                    title="FG, Labor Reach Deal on ₦70k Minimum Wage",
                    url=article_url,
                    content="Full content of the article...",
                    published_at=datetime.utcnow(),
                    description="The Federal Government has finally agreed to pay N70,000 as the new minimum wage.",
                    category="Economy"
                )
                db.add(article)
                try:
                    await db.flush()
                except Exception as e:
                    # Safe print for Windows terminals
                    print("Article exists (caught unique violation)")
                    await db.rollback()
                    stmt = select(RawArticle).where(RawArticle.url == article_url)
                    article = (await db.execute(stmt)).scalar_one_or_none()
            
            if article:
                # Associate
                stmt = select(TopicArticle).where(TopicArticle.topic_id == topic.id, TopicArticle.article_id == article.id)
                assoc = (await db.execute(stmt)).scalar_one_or_none()
                
                if not assoc:
                    assoc = TopicArticle(
                        topic_id=topic.id,
                        article_id=article.id,
                        is_primary=True,
                        relevance_score=1.0
                    )
                    db.add(assoc)
                    print("Created hero article association")
                else:
                    print("Association already exists")
            else:
                 print("Could not create or find article.")


        await db.commit()
        print("Hero data seeded successfully.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_hero_data())
