"""
STAGE 1 — ARTICLE INGESTION VALIDATION
Validates: raw article counts, text quality, encoding, HTML residue, truncation
"""
import asyncio
import os
import sys
import re
import io

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import text
from app.database import AsyncSessionLocal

HTML_TAG_RE = re.compile(r'<[^>]+>')
ENTITY_RE = re.compile(r'&[a-z]+;|&#\d+;')


async def stage1_validate():
    async with AsyncSessionLocal() as session:
        print("=" * 60)
        print("STAGE 1 — ARTICLE INGESTION VALIDATION")
        print("=" * 60)

        # ── 1. Raw article count ──────────────────────────────────
        r = await session.execute(text("SELECT COUNT(*) FROM raw_articles"))
        total_raw = r.scalar()
        print(f"\n[1] Total raw_articles:  {total_raw}")

        if total_raw == 0:
            print("  ⚠️  NO ARTICLES FOUND — pipeline has not ingested data yet.")
            return

        # ── 2. Source attribution ────────────────────────────────
        r = await session.execute(text("""
            SELECT source_id, COUNT(*) AS cnt
            FROM raw_articles
            GROUP BY source_id
            ORDER BY cnt DESC
            LIMIT 10
        """))
        rows = r.fetchall()
        print(f"\n[2] Articles per source (top 10):")
        for row in rows:
            print(f"    source_id={row[0]}  count={row[1]}")

        # ── 3. Duplication check ─────────────────────────────────
        r = await session.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT url, COUNT(*) AS c
                FROM raw_articles
                GROUP BY url
                HAVING COUNT(*) > 1
            ) dupes
        """))
        dup_count = r.scalar()
        print(f"\n[3] Duplicate URLs:       {dup_count}")

        # ── 4. Empty / null content ──────────────────────────────
        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_articles
            WHERE content IS NULL OR TRIM(content) = ''
        """))
        empty_content = r.scalar()

        r2 = await session.execute(text("""
            SELECT COUNT(*) FROM raw_articles
            WHERE title IS NULL OR TRIM(title) = ''
        """))
        empty_title = r2.scalar()
        print(f"\n[4] Empty content rows:   {empty_content}")
        print(f"    Empty title rows:     {empty_title}")

        # ── 5. Truncated content (< 100 chars) ───────────────────
        r = await session.execute(text("""
            SELECT COUNT(*) FROM raw_articles
            WHERE content IS NOT NULL AND LENGTH(TRIM(content)) < 100
        """))
        truncated = r.scalar()
        print(f"\n[5] Truncated content (<100 chars): {truncated}")

        # ── 6. HTML residue check ────────────────────────────────
        r = await session.execute(text("""
            SELECT id, title, SUBSTRING(content, 1, 300) AS snippet
            FROM raw_articles
            WHERE content ~ '<[^>]+>'
            LIMIT 5
        """))
        html_rows = r.fetchall()
        print(f"\n[6] Articles with HTML tags: {len(html_rows)} (sample shown)")
        for row in html_rows:
            print(f"    id={row[0]} | title={row[1][:60]}")
            print(f"    snippet: {row[2][:120]}")

        # ── 7. Encoding issues (replacement chars) ────────────────
        r = await session.execute(text(r"""
            SELECT COUNT(*) FROM raw_articles
            WHERE content LIKE '%\uFFFD%' OR content LIKE '%â%'
        """))
        encoding_issues = r.scalar()
        print(f"\n[7] Possible encoding issues: {encoding_issues}")

        # ── 8. Sample cleaned article preview ────────────────────
        r = await session.execute(text("""
            SELECT id, title, published_at, source_id, LENGTH(content) AS len,
                   SUBSTRING(content, 1, 400) AS preview
            FROM raw_articles
            WHERE content IS NOT NULL AND LENGTH(content) > 200
            ORDER BY published_at DESC
            LIMIT 3
        """))
        samples = r.fetchall()
        print(f"\n[8] Sample article previews (latest 3):")
        for s in samples:
            print(f"\n  ── id={s[0]} | source_id={s[3]} | content_len={s[4]}")
            print(f"     Title: {s[1]}")
            print(f"     Published: {s[2]}")
            print(f"     Preview: {s[5][:300]}")

        # ── 9. Normalized articles check ─────────────────────────
        # Check if a normalized / cleaned version table exists
        for tbl in ["normalized_articles", "cleaned_articles"]:
            r = await session.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = '{tbl}'
                )
            """))
            exists = r.scalar()
            if exists:
                r2 = await session.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
                cnt = r2.scalar()
                print(f"\n[9] {tbl} count: {cnt}")
            else:
                print(f"\n[9] Table '{tbl}' does not exist (may use raw_articles directly).")

        # ── Summary ───────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("STAGE 1 SUMMARY")
        print("=" * 60)
        print(f"  Total raw articles:      {total_raw}")
        print(f"  Duplicate URLs:          {dup_count}")
        print(f"  Empty content records:   {empty_content}")
        print(f"  Empty title records:     {empty_title}")
        print(f"  Truncated (<100 chars):  {truncated}")
        print(f"  HTML-residue records:    {len(html_rows)} (sampled)")
        print(f"  Encoding issues:         {encoding_issues}")
        print("=" * 60)
        print("\n✅ STAGE 1 COMPLETE — Awaiting review before Stage 2.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(stage1_validate())
