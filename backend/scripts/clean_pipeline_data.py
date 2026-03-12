#!/usr/bin/env python3
"""
clean_pipeline_data.py
======================
Wipes all AI pipeline-generated data tables so the pipeline can
re-run from scratch on GCP with fresh records.

PRESERVED (config tables — NOT touched):
  - sources              (news source configs)
  - source_groups        (source grouping config)
  - source_group_members (source group memberships)
  - categories           (if any)
  - category_configs     (AI dimension configs per category)
  - impact_categories    (impact type config)
  - users                (user accounts)
  - ads                  (ad configs)
  - settings / ai_usage_configs

DELETED (pipeline data tables):
  - raw_articles                 (fetched articles)
  - youtube_videos               (YouTube data)
  - article_entities             (NLP entities)
  - article_embeddings           (vector embeddings)
  - collection_jobs              (fetch job logs)
  - sentiment_analysis           (article-level sentiment)
  - topics                       (AI-generated topics, cascades all children)
  - topic_articles               (article <-> topic links)
  - topic_analysis               (AI analysis per topic)
  - topic_sentiment_breakdown    (dimension sentiment per topic)
  - ai_summaries                 (AI summary text)
  - summary_updates              (summary update log)
  - topic_trends                 (trend data)
  - topic_videos                 (topic video links)
  - topic_perspectives           (source group perspectives)
  - perspective_quotes           (perspective quotes)
  - source_perspectives          (per-source framing)
  - intelligence_cards           (homepage intel cards)
  - regional_impacts             (impact items per topic)
  - impact_details               (impact detail rows)
  - impact_metrics               (impact metrics)
  - polls                        (AI-generated polls)
  - poll_options                 (poll options)
  - poll_votes                   (poll votes)
  - comments                     (user comments)
  - comment_votes                (comment votes)
  - community_insights           (AI-flagged insights)
  - topic_tags                   (topic tags)
  - jobs                         (background job records)

Usage:
    python scripts/clean_pipeline_data.py
    python scripts/clean_pipeline_data.py --dry-run
"""

import sys
import argparse
from sqlalchemy import text
from app.database import SessionLocal

# ────────────────────────────────────────────────────────────────────────────
# ORDER MATTERS: delete child tables before parent tables to avoid FK errors.
# All children of Topic are also cleaned via CASCADE, but we list them
# explicitly first for safety when running TRUNCATE rather than DELETE.
# ────────────────────────────────────────────────────────────────────────────

PIPELINE_TABLES = [
    # Level 3 (deepest children)
    "poll_votes",
    "poll_options",
    "comment_votes",
    "community_insights",
    "perspective_quotes",
    "impact_details",

    # Level 2 (children of topics / articles)
    "article_entities",
    "article_embeddings",
    "youtube_videos",
    "sentiment_analysis",
    "topic_articles",
    "topic_analysis",
    "topic_sentiment_breakdown",
    "ai_summaries",
    "summary_updates",
    "topic_trends",
    "topic_videos",
    "topic_perspectives",
    "source_perspectives",
    "intelligence_cards",
    "regional_impacts",
    "impact_metrics",
    "polls",
    "comments",
    "topic_tags",

    # Level 1 (root pipeline tables)
    "raw_articles",
    "topics",
    "collection_jobs",
    "jobs",
]


def confirm_deletion() -> bool:
    print("\n⚠️  WARNING: This will permanently delete ALL pipeline data from the database.")
    print("    Config tables (sources, categories, users, etc.) will NOT be affected.")
    print()
    answer = input("    Type 'yes' to confirm: ").strip().lower()
    return answer == "yes"


def clean_pipeline_data(dry_run: bool = False):
    db = SessionLocal()
    try:
        if not dry_run and not confirm_deletion():
            print("\n❌ Aborted — no data was deleted.")
            return

        print()
        total_deleted = 0

        for table in PIPELINE_TABLES:
            try:
                if dry_run:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  [DRY-RUN] {table}: {count} rows would be deleted")
                else:
                    result = db.execute(text(f"DELETE FROM {table}"))
                    rows = result.rowcount
                    total_deleted += rows
                    print(f"  ✓ {table}: {rows} rows deleted")
            except Exception as e:
                print(f"  ✗ {table}: ERROR — {e}")
                db.rollback()
                raise

        if not dry_run:
            db.commit()
            print(f"\n✅ Done! {total_deleted} total rows deleted across {len(PIPELINE_TABLES)} tables.")
            print("   The pipeline is ready for a fresh run.\n")
        else:
            print(f"\n[DRY-RUN COMPLETE] No changes were made.\n")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean AI pipeline data tables.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting anything.",
    )
    args = parser.parse_args()
    clean_pipeline_data(dry_run=args.dry_run)
