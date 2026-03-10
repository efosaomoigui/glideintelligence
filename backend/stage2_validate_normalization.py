"""
STAGE 2 — NORMALIZATION + EMBEDDING FLOW VALIDATION
Verifies: embedding count, category assignment, content quality, title consistency
"""
import asyncio
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def stage2_validate():
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("STAGE 2 — NORMALIZATION + EMBEDDING FLOW")
        print("=" * 60)

        # ── 1. Raw vs Embedded counts ──────────────────────────────
        r = await session.execute(text("SELECT COUNT(*) FROM raw_articles"))
        total_raw = r.scalar()

        r = await session.execute(text("SELECT COUNT(*) FROM article_embeddings"))
        total_embed = r.scalar()

        print(f"\n[1] raw_articles:        {total_raw}")
        print(f"    article_embeddings:  {total_embed}")
        
        coverage = (total_embed / total_raw * 100) if total_raw > 0 else 0
        status = "✅" if coverage >= 95 else ("⚠️" if coverage >= 80 else "🔴")
        print(f"    Coverage:            {coverage:.1f}% {status}")

        missing = total_raw - total_embed
        print(f"    Missing embeddings:  {missing}")

        # ── 2. Articles without embeddings ─────────────────────────
        if missing > 0:
            r = await session.execute(text("""
                SELECT ra.id, ra.title
                FROM raw_articles ra
                LEFT JOIN article_embeddings ae ON ae.article_id = ra.id
                WHERE ae.id IS NULL
                LIMIT 5
            """))
            rows = r.fetchall()
            print(f"\n[2] Sample articles missing embeddings:")
            for row in rows:
                print(f"    id={row[0]} | {row[1][:70]}")
        else:
            print(f"\n[2] All articles have embeddings ✅")

        # ── 3. Category assignment ─────────────────────────────────
        r = await session.execute(text("""
            SELECT category, COUNT(*) AS cnt
            FROM raw_articles
            GROUP BY category
            ORDER BY cnt DESC
        """))
        cats = r.fetchall()
        print(f"\n[3] Category distribution:")
        for cat in cats:
            label = cat[0] if cat[0] else "NULL/uncategorized"
            print(f"    {label:20s} : {cat[1]}")

        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_articles WHERE category IS NULL
        """))
        uncategorized = r.scalar()
        print(f"    Uncategorized total: {uncategorized}")

        # ── 4. Sentiment score (normalization marker) ──────────────
        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_articles WHERE sentiment_score IS NOT NULL
        """))
        with_sentiment = r.scalar()

        r2 = await session.execute(text("""
            SELECT COUNT(*) FROM raw_articles WHERE sentiment_score IS NULL
        """))
        without_sentiment = r2.scalar()
        print(f"\n[4] Articles marked as normalized (sentiment_score set): {with_sentiment}")
        print(f"    Still unnormalized (sentiment_score NULL):             {without_sentiment}")

        # ── 5. Embedding vector sanity check ──────────────────────
        r = await session.execute(text("""
            SELECT ae.id, ra.title,
                   LENGTH(ae.embedding::text) AS vec_len
            FROM article_embeddings ae
            JOIN raw_articles ra ON ra.id = ae.article_id
            ORDER BY ae.id DESC
            LIMIT 3
        """))
        rows = r.fetchall()
        print(f"\n[5] Sample embedding vector length check:")
        for row in rows:
            print(f"    embed_id={row[0]} | vec_text_len={row[2]} | title={row[1][:60]}")

        # ── 6. Title consistency (normalized vs. raw) ──────────────
        r = await session.execute(text("""
            SELECT id, title, LENGTH(title) AS tlen
            FROM raw_articles
            WHERE title IS NOT NULL
            ORDER BY tlen DESC
            LIMIT 5
        """))
        rows = r.fetchall()
        print(f"\n[6] Longest titles (truncation check):")
        for row in rows:
            print(f"    id={row[0]} len={row[2]} | {row[1][:80]}")

        # ── 7. Content length distribution ────────────────────────
        r = await session.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE LENGTH(content) < 100) AS tiny,
                COUNT(*) FILTER (WHERE LENGTH(content) BETWEEN 100 AND 500) AS short,
                COUNT(*) FILTER (WHERE LENGTH(content) BETWEEN 500 AND 2000) AS medium,
                COUNT(*) FILTER (WHERE LENGTH(content) > 2000) AS long
            FROM raw_articles WHERE content IS NOT NULL
        """))
        dist = r.fetchone()
        print(f"\n[7] Content length distribution:")
        print(f"    Tiny   (<100 chars):      {dist[0]}")
        print(f"    Short  (100-500 chars):   {dist[1]}")
        print(f"    Medium (500-2000 chars):  {dist[2]}")
        print(f"    Long   (>2000 chars):     {dist[3]}")

        # ── 8. Normalization bypass check ─────────────────────────
        # Any article whose content still contains raw HTML AND has been embedded
        r = await session.execute(text("""
            SELECT COUNT(*)
            FROM raw_articles ra
            INNER JOIN article_embeddings ae ON ae.article_id = ra.id
            WHERE ra.content ~ '<[^>]+'
        """))
        html_embedded = r.scalar()
        print(f"\n[8] Embedded articles that still contain HTML: {html_embedded}")
        if html_embedded > 0:
            print("    ⚠️  HTML content was passed directly into embedding — may affect clustering quality")

        # ── Summary ───────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("STAGE 2 SUMMARY")
        print("=" * 60)
        print(f"  raw_articles:              {total_raw}")
        print(f"  article_embeddings:        {total_embed}")
        print(f"  Embedding coverage:        {coverage:.1f}%")
        print(f"  Missing embeddings:        {missing}")
        print(f"  Normalized (sent. set):    {with_sentiment}")
        print(f"  Still unnormalized:        {without_sentiment}")
        print(f"  Uncategorized:             {uncategorized}")
        print(f"  HTML-contaminated embeds:  {html_embedded}")
        print("=" * 60)
        print("\n✅ STAGE 2 COMPLETE — Awaiting review before Stage 3.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(stage2_validate())
