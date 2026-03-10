"""
clean_for_fresh_start.py - Wipes all pipeline-generated data for a clean start.

PRESERVED: sources, users, ai_providers, feature_flags, category_configs,
           verticals, tags, source_groups, source_group_members

WIPED: all articles, topics, analyses (sentiment, regional, perspectives,
       impacts), intelligence cards, interactions, audit logs, jobs

LOGS CLEARED: app/logs/app.log, app/logs/error.log, app/logs/worker.log, error.log
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import AsyncSessionLocal

TABLES_TO_WIPE = [
    # Article layer
    "article_embeddings",
    "article_entities",
    "collection_jobs",
    # Topic child tables
    "topic_videos",
    "topic_trends",
    "summary_updates",
    "ai_summaries",
    "topic_sentiment_breakdown",
    "topic_analysis",
    "topic_articles",
    # AI-generated analysis
    "source_perspectives",
    "perspective_quotes",
    "topic_perspectives",
    "sentiment_analyses",
    "impact_details",
    "impact_metrics",
    "regional_impacts",
    "impact_categories",
    # Homepage cards
    "intelligence_cards",
    # Interactions
    "poll_votes",
    "poll_options",
    "polls",
    "comment_votes",
    "comments",
    "community_insights",
    "analytics_events",
    # Core content
    "topics",
    "raw_articles",
    # Operational
    "audit_logs",
    "jobs",
]

LOG_FILES = [
    os.path.join("app", "logs", "app.log"),
    os.path.join("app", "logs", "error.log"),
    os.path.join("app", "logs", "worker.log"),
    "error.log",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


async def run_cleanup():
    print("")
    print("=" * 60)
    print("  GLIDE INTELLIGENCE - FRESH START CLEANUP")
    print("=" * 60)

    async with AsyncSessionLocal() as session:

        # 1. Wipe pipeline tables
        print("\n[1/4] Wiping pipeline tables...")
        # Tables with deep FK dependents use TRUNCATE CASCADE; all others use DELETE.
        CASCADE_TABLES = {"topics", "raw_articles"}
        skipped = []
        for table in TABLES_TO_WIPE:
            try:
                if table in CASCADE_TABLES:
                    await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                    print(f"  [OK] {table:<35} (truncated with cascade)")
                else:
                    result = await session.execute(text(f"DELETE FROM {table}"))
                    print(f"  [OK] {table:<35} ({result.rowcount} rows)")
            except Exception as e:
                short = str(e).split('\n')[0][:60]
                print(f"  [--] {table:<35} SKIPPED - {short}")
                skipped.append(table)
                await session.rollback()

        await session.commit()

        # 2. Reset source fetch state
        print("\n[2/4] Resetting source fetch state...")
        try:
            r1 = await session.execute(
                text("UPDATE sources SET last_fetched_at = NULL, fetch_error_count = 0")
            )
            r2 = await session.execute(text("DELETE FROM source_health"))
            await session.commit()
            print(f"  [OK] sources reset          ({r1.rowcount} rows)")
            print(f"  [OK] source_health cleared  ({r2.rowcount} rows)")
        except Exception as e:
            await session.rollback()
            print(f"  [!!] Source reset failed: {e}")

        # 3. Verify preserved tables
        print("\n[3/4] Verifying preserved tables...")
        preserved = [
            "sources", "users", "ai_providers", "feature_flags",
            "category_configs", "verticals", "tags",
            "source_groups", "source_group_members",
        ]
        for table in preserved:
            try:
                r = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = r.scalar()
                tag = "[OK]" if count and count > 0 else "[!!] EMPTY"
                print(f"  {tag} {table:<35} {count} rows")
            except Exception as e:
                print(f"  [!!] {table:<35} ERROR: {str(e)[:50]}")

    # 4. Clear log files
    print("\n[4/4] Clearing log files...")
    for rel_path in LOG_FILES:
        full_path = os.path.join(SCRIPT_DIR, rel_path)
        try:
            if os.path.exists(full_path):
                size_before = os.path.getsize(full_path)
                with open(full_path, "w") as f:
                    f.write("")
                print(f"  [OK] {rel_path:<42} ({size_before:,} bytes cleared)")
            else:
                print(f"  [--] {rel_path:<42} not found, skipping")
        except Exception as e:
            print(f"  [!!] {rel_path:<42} ERROR: {e}")

    print("")
    print("=" * 60)
    if skipped:
        print(f"  Done. {len(skipped)} table(s) skipped: {', '.join(skipped)}")
        print("  Skipped tables may not exist yet - run migrations if needed.")
    else:
        print("  CLEAN SLATE READY.  Run pipeline in order:")
        print("    1. RSS / Website Fetch")
        print("    2. Normalize")
        print("    3. Cluster -> Topics")
        print("    4. AI Analysis")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    asyncio.run(run_cleanup())
