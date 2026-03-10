"""Check data population across key tables."""
import asyncio
import asyncpg

DB_URL = "postgresql://postgres:mysecure123@localhost:5432/news_intelligence"

async def check():
    conn = await asyncpg.connect(DB_URL)

    counts = [
        ("topics (total)", "SELECT COUNT(*) FROM topics"),
        ("topics status=stable", "SELECT COUNT(*) FROM topics WHERE status='stable'"),
        ("topics status=developing", "SELECT COUNT(*) FROM topics WHERE status='developing'"),
        ("topics with category", "SELECT COUNT(*) FROM topics WHERE category IS NOT NULL"),
        ("source_perspectives", "SELECT COUNT(*) FROM source_perspectives"),
        ("regional_impacts", "SELECT COUNT(*) FROM regional_impacts"),
        ("topic_analysis", "SELECT COUNT(*) FROM topic_analysis"),
        ("topic_sentiment_breakdown", "SELECT COUNT(*) FROM topic_sentiment_breakdown"),
        ("intelligence_cards", "SELECT COUNT(*) FROM intelligence_cards"),
        ("category_configs", "SELECT COUNT(*) FROM category_configs"),
    ]

    print("=== DATA COUNTS ===")
    for label, sql in counts:
        r = await conn.fetchval(sql)
        print(f"  {label}: {r}")

    print("\n=== SAMPLE TOPICS (latest 10) ===")
    rows = await conn.fetch(
        "SELECT id, status, category, overall_sentiment, title FROM topics ORDER BY updated_at DESC LIMIT 10"
    )
    for row in rows:
        print(f"  id={row['id']} status={row['status']} cat={row['category']} sent={row['overall_sentiment']} | {row['title'][:60]}")

    print("\n=== RECENT JOBS ===")
    rows = await conn.fetch(
        "SELECT type, status, error FROM jobs ORDER BY created_at DESC LIMIT 10"
    )
    for row in rows:
        err = str(row['error'])[:80] if row['error'] else None
        print(f"  type={row['type']} status={row['status']} error={err}")

    print("\n=== AI PROVIDERS ===")
    rows = await conn.fetch("SELECT name, type, model, is_active, priority FROM ai_providers ORDER BY priority")
    for row in rows:
        print(f"  {row['name']} | {row['type']} | {row['model']} | active={row['is_active']} | priority={row['priority']}")

    print("\n=== CATEGORY CONFIGS ===")
    rows = await conn.fetch("SELECT category FROM category_configs ORDER BY category")
    print(f"  {[r['category'] for r in rows]}")

    # Check if any topic has source_perspectives
    sp_topics = await conn.fetch(
        "SELECT DISTINCT topic_id FROM source_perspectives LIMIT 5"
    )
    print(f"\n=== TOPICS WITH source_perspectives: {[r['topic_id'] for r in sp_topics]} ===")

    ri_topics = await conn.fetch(
        "SELECT DISTINCT topic_id FROM regional_impacts LIMIT 5"
    )
    print(f"=== TOPICS WITH regional_impacts: {[r['topic_id'] for r in ri_topics]} ===")

    await conn.close()

asyncio.run(check())
