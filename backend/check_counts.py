
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_tables():
    tables = [
        "topics", "topic_articles", "topic_analysis", "topic_sentiment_breakdown",
        "ai_summaries", "summary_updates", "topic_trends", "topic_videos",
        "regional_impacts", "impact_details", "impact_metrics", "source_perspectives",
        "intelligence_cards", "jobs", "ai_usage_logs", "audit_logs", "comments",
        "comment_votes", "polls", "poll_options", "poll_votes", "community_insights",
        "raw_articles", "article_entities", "article_embeddings", "youtube_videos"
    ]
    
    async with AsyncSessionLocal() as session:
        for table in tables:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"{table}: {count}")
            except Exception as e:
                print(f"{table}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(check_tables())
