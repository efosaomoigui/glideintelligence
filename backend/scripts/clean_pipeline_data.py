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

import asyncio
import argparse
from app.database import AsyncSessionLocal
from app.services.maintenance_service import clean_pipeline_data

def confirm_deletion(bypass: bool = False) -> bool:
    if bypass:
        return True
    print("\n⚠️  WARNING: This will permanently delete ALL pipeline data from the database.")
    print("    Config tables (sources, categories, users, etc.) will NOT be affected.")
    print()
    answer = input("    Type 'yes' to confirm: ").strip().lower()
    return answer == "yes"


async def run_cleanup(dry_run: bool = False, force: bool = False):
    async with AsyncSessionLocal() as db:
        try:
            if not dry_run and not confirm_deletion(force):
                print("\n❌ Aborted — no data was deleted.")
                return

            print("\nCleaning pipeline data...")
            
            if dry_run:
                # Reuse the table list for dry-run
                from app.services.maintenance_service import PIPELINE_TABLES
                from sqlalchemy import text
                for table in PIPELINE_TABLES:
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  [DRY-RUN] {table}: {count} rows would be deleted")
                print(f"\n[DRY-RUN COMPLETE] No changes were made.\n")
            else:
                result = await clean_pipeline_data(db)
                if result["status"] == "success":
                    print(f"\n✅ Done! {result['total_deleted']} total rows deleted across {len(result['details'])} tables.")
                    print("   The pipeline is ready for a fresh run.\n")
                else:
                    print(f"\n❌ Error: {result['message']}\n")

        finally:
            await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean AI pipeline data tables.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bypass confirmation prompt.",
    )
    args = parser.parse_args()
    asyncio.run(run_cleanup(dry_run=args.dry_run, force=args.yes))
