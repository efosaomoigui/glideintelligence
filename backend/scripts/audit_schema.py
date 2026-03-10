"""
Database Schema Audit — Prompt 1 of 6
Runs all 9 checks and prints a summary report.
"""
import asyncio
import os
import sys

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed, trying psycopg2...")
    import psycopg2
    asyncpg = None

# ── helpers ──────────────────────────────────────────────────────────────────

def get_db_url():
    # Read individual vars from .env and build a proper asyncpg URL
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    user = env.get('POSTGRES_USER', 'postgres')
    pwd  = env.get('POSTGRES_PASSWORD', 'postgres')
    host = env.get('POSTGRES_HOST', 'localhost')
    port = env.get('POSTGRES_PORT', '5432')
    db   = env.get('POSTGRES_DB', 'news_intelligence')
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"


async def run_audit():
    url = get_db_url()
    print(f"Connecting to: {url[:40]}...")
    conn = await asyncpg.connect(url)

    results = {}

    # ── 1.1 Core tables ──────────────────────────────────────────────────────
    expected_tables = [
        'topics','topic_sentiment_breakdown','topic_analysis','topic_trends',
        'topic_articles','topic_videos','sources','source_health','raw_articles',
        'article_entities','article_embeddings','users','polls','poll_votes',
        'comments','jobs','ai_providers','feature_flags','audit_logs'
    ]
    rows = await conn.fetch("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY($1::text[])
        ORDER BY table_name
    """, expected_tables)
    found_tables = {r['table_name'] for r in rows}
    missing_tables = set(expected_tables) - found_tables
    critical_missing = missing_tables & {'topics','topic_sentiment_breakdown','topic_analysis','sources','raw_articles','jobs'}
    print(f"\n=== CHECK 1.1: CORE TABLES ({len(found_tables)}/19) ===")
    print(f"  Found: {sorted(found_tables)}")
    print(f"  Missing: {sorted(missing_tables)}")
    results['1.1'] = ('FAIL' if critical_missing else ('PARTIAL' if missing_tables else 'PASS'), f"Missing: {sorted(missing_tables)}" if missing_tables else "All 19 present")

    # ── 1.2 topics columns ───────────────────────────────────────────────────
    topic_cols = {r['column_name'] for r in await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name='topics'"
    )}
    needed = ['overall_sentiment','sentiment_score','view_count','engagement_count','category','slug','status']
    missing_topic_cols = [c for c in needed if c not in topic_cols]
    print(f"\n=== CHECK 1.2: topics COLUMNS ===")
    for c in needed:
        print(f"  {c}: {'EXISTS' if c in topic_cols else 'MISSING'}")
    results['1.2'] = ('PARTIAL' if missing_topic_cols else 'PASS', f"Missing: {missing_topic_cols}" if missing_topic_cols else "All present")

    # ── 1.3 topic_sentiment_breakdown ────────────────────────────────────────
    sb_cols = {r['column_name'] for r in await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name='topic_sentiment_breakdown'"
    )}
    needed_sb = ['dimension_type','dimension_value','sentiment','sentiment_score','percentage','icon','description']
    missing_sb = [c for c in needed_sb if c not in sb_cols]
    print(f"\n=== CHECK 1.3: topic_sentiment_breakdown COLUMNS ===")
    for c in ['positive','neutral','negative'] + needed_sb:
        print(f"  {c}: {'EXISTS' if c in sb_cols else 'MISSING'}")
    critical_sb = [c for c in ['dimension_type','dimension_value'] if c not in sb_cols]
    results['1.3'] = ('FAIL' if critical_sb else ('PARTIAL' if missing_sb else 'PASS'), f"Missing: {missing_sb}" if missing_sb else "All present")

    # ── 1.4 topic_analysis + source_perspectives ─────────────────────────────
    ta_cols = {r['column_name'] for r in await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name='topic_analysis'"
    )}
    sp_tables = {r['table_name'] for r in await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_name IN ('source_perspectives','topic_source_perspectives')"
    )}
    print(f"\n=== CHECK 1.4: topic_analysis + source_perspectives ===")
    print(f"  topic_analysis cols: {sorted(ta_cols)}")
    print(f"  Separate source_perspectives table: {sp_tables or 'NONE'}")
    has_ta = 'topic_analysis' in found_tables
    has_sp = bool(sp_tables)
    results['1.4'] = ('PASS' if (has_ta and ('facts' in ta_cols or has_sp)) else 'FAIL',
                      f"topic_analysis={'EXISTS' if has_ta else 'MISSING'}, source_perspectives={'EXISTS' if has_sp else 'using JSON'}")

    # ── 1.5 regional_impacts ─────────────────────────────────────────────────
    ri_tables = {r['table_name'] for r in await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_name IN ('regional_impacts','topic_regional_impacts','impact_categories','impact_details')"
    )}
    print(f"\n=== CHECK 1.5: regional_impacts ===")
    print(f"  Tables found: {ri_tables or 'NONE'}")
    for tbl in ri_tables:
        ri_cols = [r['column_name'] for r in await conn.fetch(
            f"SELECT column_name FROM information_schema.columns WHERE table_name='{tbl}'"
        )]
        print(f"  {tbl} cols: {ri_cols}")
    needed_ri = {'topic_id','icon','title','value','severity'}
    if 'regional_impacts' in ri_tables:
        ri_actual = {r['column_name'] for r in await conn.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_name='regional_impacts'"
        )}
        missing_ri = needed_ri - ri_actual
        results['1.5'] = ('PASS' if not missing_ri else 'PARTIAL', f"Missing cols: {missing_ri}" if missing_ri else "Dedicated table with correct cols")
    else:
        # Check facts JSON
        facts_row = await conn.fetchrow("SELECT facts FROM topic_analysis WHERE facts IS NOT NULL LIMIT 1") if 'topic_analysis' in found_tables else None
        results['1.5'] = ('PARTIAL' if facts_row else 'FAIL', "No dedicated table; using facts JSON" if facts_row else "No dedicated table AND facts JSON empty")

    # ── 1.6 intelligence_cards / topic_trends ────────────────────────────────
    ic_tables = {r['table_name'] for r in await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_name IN ('intelligence_cards','topic_trends')"
    )}
    print(f"\n=== CHECK 1.6: intelligence_cards / topic_trends ===")
    print(f"  Tables found: {ic_tables}")
    for tbl in ic_tables:
        ic_cols = [r['column_name'] for r in await conn.fetch(
            f"SELECT column_name FROM information_schema.columns WHERE table_name='{tbl}'"
        )]
        print(f"  {tbl} cols: {ic_cols}")
    if 'intelligence_cards' in ic_tables:
        ic_actual = {r['column_name'] for r in await conn.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_name='intelligence_cards'"
        )}
        needed_ic = {'topic_id','category','icon','title','description','trend_percentage','is_positive'}
        missing_ic = needed_ic - ic_actual
        results['1.6'] = ('PASS' if not missing_ic else 'PARTIAL', f"Missing: {missing_ic}" if missing_ic else "intelligence_cards complete")
    elif 'topic_trends' in ic_tables:
        tt_cols = {r['column_name'] for r in await conn.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_name='topic_trends'"
        )}
        has_ext = 'trend_percentage' in tt_cols and 'is_positive' in tt_cols
        results['1.6'] = ('PARTIAL' if not has_ext else 'PASS', "topic_trends lacks trend_percentage/is_positive" if not has_ext else "topic_trends extended")
    else:
        results['1.6'] = ('FAIL', "Neither intelligence_cards nor topic_trends found")

    # ── 1.7 jobs + ai_providers ──────────────────────────────────────────────
    jobs_cols = {r['column_name'] for r in await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name='jobs'"
    )}
    ai_providers = await conn.fetch("SELECT name, type, model, priority FROM ai_providers ORDER BY priority") if 'ai_providers' in found_tables else []
    print(f"\n=== CHECK 1.7: jobs + ai_providers ===")
    print(f"  jobs cols: {sorted(jobs_cols)}")
    print(f"  ai_providers ({len(ai_providers)} rows):")
    for r in ai_providers:
        print(f"    {r['name']} | {r['type']} | {r['model']} | priority={r['priority']}")
    jobs_ok = 'payload' in jobs_cols and 'result' in jobs_cols
    providers_ok = len(ai_providers) > 0
    results['1.7'] = ('PASS' if (jobs_ok and providers_ok) else ('PARTIAL' if jobs_ok else 'FAIL'),
                      f"jobs={'OK' if jobs_ok else 'missing payload/result'}, providers={len(ai_providers)}")

    # ── 1.8 category_configs ─────────────────────────────────────────────────
    cc_exists = await conn.fetchrow("SELECT table_name FROM information_schema.tables WHERE table_name='category_configs'")
    print(f"\n=== CHECK 1.8: category_configs ===")
    if cc_exists:
        cc_data = await conn.fetch("SELECT category FROM category_configs ORDER BY category")
        cats = [r['category'] for r in cc_data]
        print(f"  EXISTS, categories: {cats}")
        results['1.8'] = ('PASS' if len(cats) >= 3 else 'PARTIAL', f"Has {len(cats)} categories: {cats}")
    else:
        print("  MISSING — table does not exist")
        results['1.8'] = ('FAIL', "Table does not exist — must be created")

    # ── 1.9 indexes ──────────────────────────────────────────────────────────
    idx_rows = await conn.fetch("""
        SELECT indexname, tablename FROM pg_indexes
        WHERE schemaname='public'
          AND tablename IN ('topics','topic_sentiment_breakdown','topic_analysis','raw_articles','topic_articles','source_health')
        ORDER BY tablename, indexname
    """)
    print(f"\n=== CHECK 1.9: INDEXES ===")
    idx_by_table = {}
    for r in idx_rows:
        idx_by_table.setdefault(r['tablename'], []).append(r['indexname'])
        print(f"  {r['tablename']}: {r['indexname']}")
    critical_idx = 'topic_sentiment_breakdown' in idx_by_table
    results['1.9'] = ('PASS' if critical_idx else 'PARTIAL', "topic_sentiment_breakdown index missing" if not critical_idx else "Critical indexes present")

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("AUDIT SUMMARY")
    print("="*70)
    print(f"{'Check':<8} {'Status':<10} Notes")
    print("-"*70)
    descs = {
        '1.1': 'Core tables exist (19)',
        '1.2': 'topics has required columns',
        '1.3': 'sentiment_breakdown dimension cols',
        '1.4': 'topic_analysis / source_perspectives',
        '1.5': 'regional_impacts table or JSON',
        '1.6': 'intelligence_cards / topic_trends',
        '1.7': 'jobs table + ai_providers',
        '1.8': 'category_configs created & seeded',
        '1.9': 'Performance indexes',
    }
    passed = 0
    for k in sorted(results):
        status, note = results[k]
        if status == 'PASS': passed += 1
        print(f"{k:<8} {status:<10} {note}")
    print(f"\nOVERALL: {passed}/9 checks passed")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(run_audit())
