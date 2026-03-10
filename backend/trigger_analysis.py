import asyncio
import os
import sys

sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.config import settings
from app.services.ai.summarization_service import SummarizationService
from app.models import Topic, TopicAnalysis, TopicArticle, RawArticle, AISummary, TopicSentimentBreakdown
from datetime import datetime

async def trigger_analysis():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Initializing SummarizationService...")
        ai_svc = SummarizationService(session)
        
        # Find topics without analysis
        query = select(Topic).outerjoin(TopicAnalysis).where(TopicAnalysis.id == None)
        result = await session.execute(query)
        topics = result.scalars().all()
        
        print(f"Found {len(topics)} topics to analyze.")
        
        for topic in topics:
            safe_title = topic.title.encode('ascii', 'ignore').decode('ascii')
            print(f"Analyzing Topic {topic.id}: {safe_title}...")
            try:
                # 1. Fetch topic articles
                query = select(RawArticle.content).join(TopicArticle).where(TopicArticle.topic_id == topic.id)
                result = await session.execute(query)
                contents = [c for c in result.scalars().all() if c]
                
                if not contents:
                    print(f"  No content found for topic {topic.id}")
                    continue
                
                # 2. Run AI pipeline
                analysis_data = await ai_svc.generate_summary_pipeline(contents)
                print(f"  Analysis generated (Provider: {analysis_data.get('provider')})")
                
                # 3. Save results
                # A. Current Snapshot
                analysis = TopicAnalysis(
                    topic_id=topic.id,
                    summary=analysis_data["summary"],
                    facts=analysis_data["facts"],
                    regional_framing=analysis_data["regional_framing"]
                )
                session.add(analysis)
                
                # B. Historical Record
                ai_summary = AISummary(
                    topic_id=topic.id,
                    summary_type="60_second",
                    content=analysis_data["summary"],
                    bullet_points=analysis_data.get("facts", []),
                    model_used=analysis_data.get("provider", "Unknown"),
                    quality_score=analysis_data.get("confidence_score", 0.0),
                    is_current=True,
                    generated_at=datetime.now()
                )
                session.add(ai_summary)
                
                # C. Sentiment
                sentiment = TopicSentimentBreakdown(
                    topic_id=topic.id,
                    positive=analysis_data["sentiment"]["positive"],
                    neutral=analysis_data["sentiment"]["neutral"],
                    negative=analysis_data["sentiment"]["negative"]
                )
                session.add(sentiment)
                
                # D. Update Topic
                topic.status = "stable"
                topic.last_verified_at = datetime.now()
                
                await session.commit()
                print("  Results saved.")
                
                # Sleep to avoid hitting Gemini free tier rate limits
                import time
                print("  Sleeping for 15s to respect rate limits...")
                time.sleep(15)
                
            except Exception as e:
                print(f"Error analyzing topic {topic.id}: {e}")
                import traceback
                traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(trigger_analysis())
