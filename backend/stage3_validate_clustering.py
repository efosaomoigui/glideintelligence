"""
stage3_validate_clustering.py
Validates topic clustering, title quality, category propagation, and
checks for common clustering issues like singletons and bad titles.
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import AsyncSessionLocal

SEP = "=" * 60

async def validate():
    print("")
    print(SEP)
    print("STAGE 3 - CLUSTERING VALIDATION")
    print(SEP)

    async with AsyncSessionLocal() as s:

        # [1] Topic count
        r = await s.execute(text("SELECT COUNT(*) FROM topics"))
        topic_count = r.scalar()

        r2 = await s.execute(text("SELECT COUNT(*) FROM topic_articles"))
        link_count = r2.scalar()

        r3 = await s.execute(text(
            "SELECT COUNT(DISTINCT article_id) FROM topic_articles"
        ))
        clustered_articles = r3.scalar()

        r4 = await s.execute(text("SELECT COUNT(*) FROM article_embeddings"))
        total_embeddings = r4.scalar()

        unclustered = total_embeddings - clustered_articles
        pct = (clustered_articles / max(1, total_embeddings)) * 100

        print(f"\n[1] Topics created:          {topic_count}")
        print(f"    topic_articles links:    {link_count}")
        print(f"    Embedded articles:       {total_embeddings}")
        print(f"    Clustered articles:      {clustered_articles} ({pct:.1f}%)")
        status = "[OK]" if unclustered == 0 else "[WARN]"
        print(f"    Unclustered articles:    {unclustered} {status}")

        # [2] Articles per topic distribution
        r = await s.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE cnt = 1)   AS singletons,
                COUNT(*) FILTER (WHERE cnt = 2)   AS pairs,
                COUNT(*) FILTER (WHERE cnt BETWEEN 3 AND 5) AS small,
                COUNT(*) FILTER (WHERE cnt > 5)   AS large
            FROM (
                SELECT topic_id, COUNT(*) AS cnt
                FROM topic_articles
                GROUP BY topic_id
            ) sub
        """))
        dist = r.fetchone()
        singleton_pct = (dist[0] / max(1, topic_count)) * 100
        singleton_warn = "[WARN - too many!]" if singleton_pct > 60 else "[OK]"
        print(f"\n[2] Topic size distribution:")
        print(f"    Singleton  (1 article):  {dist[0]} ({singleton_pct:.0f}%) {singleton_warn}")
        print(f"    Pairs      (2 articles): {dist[1]}")
        print(f"    Small      (3-5):        {dist[2]}")
        print(f"    Large      (>5):         {dist[3]}")

        # [3] Category coverage on topics
        r = await s.execute(text("""
            SELECT category, COUNT(*) AS cnt
            FROM topics
            GROUP BY category
            ORDER BY cnt DESC
        """))
        rows = r.fetchall()
        print(f"\n[3] Topic category distribution:")
        for row in rows:
            label = row[0] if row[0] else "NULL (uncategorized)"
            flag = "[MISSING]" if row[0] is None else "[OK]"
            print(f"    {flag} {label:<25} {row[1]}")

        # [4] Topics with bad/copied titles (sample smallest)
        r = await s.execute(text("""
            SELECT t.id, t.title, t.category, COUNT(ta.article_id) AS articles
            FROM topics t
            LEFT JOIN topic_articles ta ON ta.topic_id = t.id
            GROUP BY t.id, t.title, t.category
            ORDER BY articles ASC
            LIMIT 10
        """))
        sample_topics = r.fetchall()
        print(f"\n[4] Sample topics (fewest articles first - check title quality):")
        for row in sample_topics:
            cat = row[2] or "no-cat"
            title = (str(row[1]) or "")[:70]
            print(f"    id={row[0]} | [{cat}] | {row[3]} arts | {title}")

        # [5] Topics without analysis
        r = await s.execute(text("""
            SELECT COUNT(*) FROM topics t
            LEFT JOIN topic_analysis ta ON ta.topic_id = t.id
            WHERE ta.id IS NULL
        """))
        without_analysis = r.scalar()

        r2 = await s.execute(text("SELECT COUNT(*) FROM topic_analysis"))
        with_analysis = r2.scalar()

        analysis_flag = "[OK]" if without_analysis == 0 else "[FAIL]"
        print(f"\n[5] AI Analysis coverage:")
        print(f"    Topics with analysis:    {with_analysis}")
        print(f"    Topics WITHOUT analysis: {without_analysis} {analysis_flag}")

        # [6] FAILED jobs - all types
        r = await s.execute(text("""
            SELECT type, status, error, started_at
            FROM jobs
            WHERE status = 'FAILED'
            ORDER BY started_at DESC
            LIMIT 10
        """))
        failed_jobs = r.fetchall()
        print(f"\n[6] FAILED jobs ({len(failed_jobs)} found):")
        if failed_jobs:
            for row in failed_jobs:
                started = str(row[3])[:19] if row[3] else "N/A"
                err = (str(row[2]) or "no error")[:70]
                print(f"    [{started}] {str(row[0]):<22} | {err}")
        else:
            print("    None! [OK]")

        # [7] AI usage logs
        r = await s.execute(text("SELECT COUNT(*) FROM ai_usage_logs"))
        usage_count = r.scalar()
        r2 = await s.execute(text(
            "SELECT COALESCE(SUM(tokens_used), 0), COALESCE(SUM(cost_usd), 0.0) FROM ai_usage_logs"
        ))
        totals = r2.fetchone()
        usage_flag = "[WARN - nothing persisted!]" if usage_count == 0 else "[OK]"
        print(f"\n[7] AI Usage Logs:")
        print(f"    Total log entries:       {usage_count} {usage_flag}")
        print(f"    Total tokens logged:     {totals[0]:,}")
        print(f"    Total cost logged:       ${totals[1]:.4f}")

        # Summary
        print(f"\n{SEP}")
        print("STAGE 3 SUMMARY")
        print(SEP)
        print(f"  Topics:                    {topic_count}")
        print(f"  Embeddings clustered:      {clustered_articles} / {total_embeddings} ({pct:.1f}%)")
        print(f"  Singleton topics:          {dist[0]} ({singleton_pct:.0f}%)")
        print(f"  Topics with analysis:      {with_analysis} / {topic_count}")
        print(f"  FAILED jobs:               {len(failed_jobs)}")
        print(f"  AI usage log entries:      {usage_count}")
        print(SEP)
        print("\nSTAGE 3 COMPLETE - Awaiting review before Stage 4.\n")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(validate())
