"""
fix_category_values.py

One-time cleanup: migrate any non-canonical category values in raw_articles
and topics to the official slugs defined in constants.py.

Canonical slugs: politics, economy, business, technology, sports,
                 security, regional, environment, social, general
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import AsyncSessionLocal

# Mapping: any bad value -> canonical slug
MIGRATIONS = {
    # wrong case
    "Politics":      "politics",
    "Economy":       "economy",
    "Business":      "business",
    "Technology":    "technology",
    "Sports":        "sports",
    "Security":      "security",
    "Regional":      "regional",
    "Environment":   "environment",
    "Social":        "social",
    "General":       "general",
    # wrong names
    "tech":          "technology",
    "Tech":          "technology",
    "crime":         "security",
    "Crime":         "security",
    "health":        "social",
    "Health":        "social",
    "finance":       "economy",
    "Finance":       "economy",
    "entertainment": "social",
    "Entertainment": "social",
    "breaking news": "general",
    "Breaking News": "general",
    "deep dive":     "general",
    "Deep Dive":     "general",
}

async def fix_categories():
    print("")
    print("=" * 60)
    print("  CATEGORY VALUE CLEANUP")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        total_fixed = 0

        for bad_val, canonical in MIGRATIONS.items():
            # raw_articles
            r1 = await session.execute(
                text("UPDATE raw_articles SET category = :good WHERE category = :bad"),
                {"good": canonical, "bad": bad_val}
            )
            if r1.rowcount:
                print(f"  raw_articles:  '{bad_val}' -> '{canonical}'  ({r1.rowcount} rows)")
                total_fixed += r1.rowcount

            # topics
            r2 = await session.execute(
                text("UPDATE topics SET category = :good WHERE category = :bad"),
                {"good": canonical, "bad": bad_val}
            )
            if r2.rowcount:
                print(f"  topics:        '{bad_val}' -> '{canonical}'  ({r2.rowcount} rows)")
                total_fixed += r2.rowcount

        await session.commit()

        # Verify final state
        print("\n  Final category distribution in raw_articles:")
        r = await session.execute(text(
            "SELECT category, COUNT(*) FROM raw_articles "
            "GROUP BY category ORDER BY COUNT(*) DESC"
        ))
        for row in r.fetchall():
            label = row[0] if row[0] else "NULL"
            print(f"    {label:<20} {row[1]}")

        print("\n  Final category distribution in topics:")
        r = await session.execute(text(
            "SELECT category, COUNT(*) FROM topics "
            "GROUP BY category ORDER BY COUNT(*) DESC"
        ))
        for row in r.fetchall():
            label = row[0] if row[0] else "NULL"
            print(f"    {label:<20} {row[1]}")

    print(f"\n  Total rows fixed: {total_fixed}")
    print("=" * 60)
    print("")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_categories())
