from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# ORDER MATTERS: delete children BEFORE parents to avoid Foreign Key errors.
# ────────────────────────────────────────────────────────────────────────────

PIPELINE_TABLES = [
    # Level 4 (Leaf children with nested FKs)
    "poll_votes",               # FK -> poll_options
    "comment_votes",            # FK -> comments
    "perspective_quotes",       # FK -> topic_perspectives
    "impact_details",           # FK -> regional_impacts
    "summary_updates",          # FK -> ai_summaries
    "ad_events",                # FK -> ads (Transient logs)

    # Level 3 (Direct children of topics/articles)
    "poll_options",             # FK -> polls
    "source_health",            # FK -> sources (Transient crawler state)
    "article_entities",         # FK -> raw_articles
    "article_embeddings",       # FK -> raw_articles
    "youtube_videos",           # FK -> raw_articles
    "sentiment_analysis",       # FK -> raw_articles
    "topic_articles",           # FK -> topics & raw_articles
    "topic_analysis",           # FK -> topics
    "topic_sentiment_breakdown",# FK -> topics
    "topic_regional_categories",# FK -> topics
    "ai_summaries",             # FK -> topics
    "topic_trends",             # FK -> topics
    "topic_videos",             # FK -> topics
    "topic_perspectives",       # FK -> topics & source_groups
    "source_perspectives",      # FK -> topics
    "intelligence_cards",       # FK -> topics
    "regional_impacts",         # FK -> topics
    "impact_metrics",           # FK -> topics
    "ai_usage_logs",            # FK -> topics
    "topic_tags",               # FK -> topics & tags
    "community_insights",       # FK -> articles (usually raw_articles or entities)

    # Level 2 (Intermediate Parents)
    "polls",                    # FK -> topics
    "comments",                 # FK -> topics
    
    # Level 1 (Root Pipeline Tables)
    "raw_articles",             # Root for articles
    "topics",                   # Root for AI content
    "collection_jobs",          # Log for fetches
    "jobs",                     # Celery job records
    "analytics_events",         # Transient logs
    "audit_logs",               # Action logs
]

async def clean_pipeline_data(db: AsyncSession) -> dict:
    """
    Wipes all AI pipeline-generated data tables.
    Returns a summary of deleted rows.
    """
    total_deleted = 0
    details = {}

    try:
        # We use a single transaction loop. 
        # If ANY table fails, the entire operation should ROLLBACK.
        for table in PIPELINE_TABLES:
            result = await db.execute(text(f"DELETE FROM {table}"))
            rows = result.rowcount
            # rowcount might be -1 or 0 if nothing deleted, that's fine.
            count = rows if rows and rows > 0 else 0
            total_deleted += count
            details[table] = count
            logger.info(f"Cleaned table {table}: {count} rows deleted")

        await db.commit()
        return {
            "status": "success",
            "total_deleted": total_deleted,
            "details": details
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Critical error during pipeline cleanup: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
