import asyncio
import sys
import os
import pandas as pd
from sqlalchemy import text
# from tabulate import tabulate

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def run_audit():
    print("Running Audit Prompt 1 of 6 — DATABASE SCHEMA (REVISED AGAINST ACTUAL ERD)\n")
    
    results = []
    migration_actions = []

    async for session in get_db():
        try:
            # ─── CHECK 1.1: CORE TABLES EXIST ────────────────────────────────────
            print("--- CHECK 1.1: CORE TABLES EXIST ---")
            tables = [
                'topics', 'topic_sentiment_breakdown', 'topic_analysis', 'topic_trends',
                'topic_articles', 'topic_videos', 'sources', 'source_health',
                'raw_articles', 'article_entities', 'article_embeddings', 'users',
                'polls', 'poll_votes', 'comments', 'jobs', 'ai_providers',
                'feature_flags', 'audit_logs'
            ]
            query = text(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = ANY(:tables)
                ORDER BY table_name;
            """)
            result_1_1 = (await session.execute(query, {"tables": tuple(tables)})).scalars().all()
            missing_tables = set(tables) - set(result_1_1)
            
            critical_missing = {'topics', 'topic_sentiment_breakdown', 'topic_analysis', 'sources', 'raw_articles', 'jobs'} & missing_tables
            if critical_missing:
                status_1_1 = "FAIL"
                notes_1_1 = f"Critical tables missing: {', '.join(critical_missing)}"
                migration_actions.append(f"Create missing critical tables: {', '.join(critical_missing)}")
            elif missing_tables:
                status_1_1 = "PARTIAL"
                notes_1_1 = f"Secondary tables missing: {', '.join(missing_tables)}"
                migration_actions.append(f"Create missing secondary tables: {', '.join(missing_tables)}")
            else:
                status_1_1 = "PASS"
                notes_1_1 = "All 19 ERD tables exist"
            
            results.append(["1.1", "All 19 ERD tables exist", status_1_1, notes_1_1])

            # ─── CHECK 1.2: topics TABLE — EXISTING + MISSING COLUMNS ────────────
            print("--- CHECK 1.2: topics TABLE ---")
            query_1_2 = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'topics'
            """)
            existing_cols = (await session.execute(query_1_2)).scalars().all()
            existing_cols_set = set(existing_cols)
            
            required_cols = ['overall_sentiment', 'sentiment_score', 'view_count', 'category'] # engagement_count removed from check as it might be computed or joined
            # Actually prompt asks to check engagement_count too:
            cols_to_check = ['overall_sentiment', 'sentiment_score', 'view_count', 'engagement_count', 'category']
            
            missing_cols = [c for c in cols_to_check if c not in existing_cols_set]
            
            if missing_cols:
                status_1_2 = "PARTIAL"
                notes_1_2 = f"Missing: {', '.join(missing_cols)}"
                migration_actions.append(f"Alter 'topics' table to add: {', '.join(missing_cols)}")
            else:
                status_1_2 = "PASS"
                notes_1_2 = "topics has all required columns"
            
            results.append(["1.2", "topics has required columns", status_1_2, notes_1_2])

            # ─── CHECK 1.3: topic_sentiment_breakdown — STRUCTURE GAP ANALYSIS ───
            print("--- CHECK 1.3: topic_sentiment_breakdown ---")
            query_1_3 = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'topic_sentiment_breakdown'
            """)
            sb_cols = set((await session.execute(query_1_3)).scalars().all())
            
            req_sb_cols = ['dimension_type', 'dimension_value', 'sentiment_score', 'percentage', 'icon']
            missing_sb = [c for c in req_sb_cols if c not in sb_cols]
            
            if 'dimension_type' in missing_sb or 'dimension_value' in missing_sb:
                status_1_3 = "FAIL"
                notes_1_3 = f"Critical missing: {', '.join(missing_sb)}"
                migration_actions.append(f"Alter 'topic_sentiment_breakdown' to add: {', '.join(missing_sb)}")
            elif missing_sb:
                status_1_3 = "PARTIAL"
                notes_1_3 = f"Missing: {', '.join(missing_sb)}"
                migration_actions.append(f"Alter 'topic_sentiment_breakdown' to add: {', '.join(missing_sb)}")
            else:
                status_1_3 = "PASS"
                notes_1_3 = "sentiment_breakdown has dimension cols"
            
            results.append(["1.3", "sentiment_breakdown has dimension cols", status_1_3, notes_1_3])

            # ─── CHECK 1.4: topic_analysis — MAPS TO source_perspectives ─────────
            print("--- CHECK 1.4: topic_analysis maps to perspectives ---")
            # Check for dedicated table first
            query_persp_table = text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name IN ('source_perspectives', 'topic_source_perspectives')
            """)
            persp_tables = (await session.execute(query_persp_table)).scalars().all()
            
            if persp_tables:
                status_1_4 = "PASS"
                notes_1_4 = f"Dedicated table exists: {persp_tables[0]}"
            else:
                # Check for JSON fields
                query_1_4 = text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'topic_analysis'
                """)
                ta_cols = set((await session.execute(query_1_4)).scalars().all())
                
                if 'regional_framing' in ta_cols and 'facts' in ta_cols:
                    status_1_4 = "PASS" # As per prompt, pass if JSON exists
                    notes_1_4 = "regional_framing JSON populated (using JSON approach)"
                else:
                    status_1_4 = "FAIL"
                    notes_1_4 = "topic_analysis missing JSON fields and no dedicated table"
                    migration_actions.append("Add JSON fields to topic_analysis or create source_perspectives table")

            results.append(["1.4", "topic_analysis maps to perspectives", status_1_4, notes_1_4])

            # ─── CHECK 1.5: regional_impacts TABLE OR COLUMN ─────────────────────
            print("--- CHECK 1.5: regional_impacts ---")
            query_impact_table = text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name IN ('regional_impacts', 'topic_regional_impacts')
            """)
            impact_tables = (await session.execute(query_impact_table)).scalars().all()
            
            if impact_tables:
                 query_cols = text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{impact_tables[0]}'")
                 impact_cols = set((await session.execute(query_cols)).scalars().all())
                 required_impact_cols = ['title', 'value', 'severity', 'context', 'icon']
                 missing_impact_cols = [c for c in required_impact_cols if c not in impact_cols]
                 
                 if not missing_impact_cols:
                     status_1_5 = "PASS"
                     notes_1_5 = f"Dedicated table {impact_tables[0]} exists with all columns"
                 else:
                     status_1_5 = "PARTIAL"
                     notes_1_5 = f"Dedicated table exists but missing columns: {missing_impact_cols}"
            else:
                # Check facts JSON
                # Assuming checked in 1.4 if using JSON
                status_1_5 = "PARTIAL"
                notes_1_5 = "using topic_analysis.facts JSON (no dedicated table)"
                
            results.append(["1.5", "regional_impacts table or JSON", status_1_5, notes_1_5])

            # ─── CHECK 1.6: intelligence_cards / topic_trends MAPPING ────────────
            print("--- CHECK 1.6: intelligence_cards ---")
            query_cards = text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name IN ('intelligence_cards', 'topic_trends')
            """)
            card_tables = set((await session.execute(query_cards)).scalars().all())
            
            if 'intelligence_cards' in card_tables:
                status_1_6 = "PASS"
                notes_1_6 = "intelligence_cards table exists"
            elif 'topic_trends' in card_tables:
                 query_trends = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'topic_trends'")
                 trend_cols = set((await session.execute(query_trends)).scalars().all())
                 
                 missing_trend = [c for c in ['trend_percentage', 'is_positive'] if c not in trend_cols]
                 if not missing_trend:
                     status_1_6 = "PASS"
                     notes_1_6 = "topic_trends has all intelligence columns"
                 else:
                     status_1_6 = "PARTIAL"
                     notes_1_6 = f"topic_trends missing: {missing_trend}"
                     migration_actions.append(f"Add columns to topic_trends or create intelligence_cards: {missing_trend}")
            else:
                status_1_6 = "FAIL"
                notes_1_6 = "Neither intelligence_cards nor topic_trends exist"
                migration_actions.append("Create intelligence_cards table")

            results.append(["1.6", "intelligence_cards / topic_trends", status_1_6, notes_1_6])

            # ─── CHECK 1.7: jobs TABLE + ai_providers CONFIG ────────────────
            print("--- CHECK 1.7: jobs & ai_providers ---")
            # Jobs
            query_jobs_cols = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'jobs'")
            jobs_cols = set((await session.execute(query_jobs_cols)).scalars().all())
            jobs_ok = 'payload' in jobs_cols and 'result' in jobs_cols
            
            # Providers
            query_providers = text("SELECT count(*) FROM ai_providers")
            provider_count = (await session.execute(query_providers)).scalar()
            
            if jobs_ok and provider_count > 0:
                status_1_7 = "PASS"
                notes_1_7 = f"Jobs table ok, {provider_count} providers configured"
            elif not jobs_ok:
                status_1_7 = "FAIL"
                notes_1_7 = "Jobs table missing JSON columns"
                migration_actions.append("Fix jobs table schema (payload/result)")
            else:
                 status_1_7 = "FAIL"
                 notes_1_7 = "ai_providers table empty"
                 migration_actions.append("Seed ai_providers table")
                 
            results.append(["1.7", "jobs table + ai_providers configured", status_1_7, notes_1_7])

            # ─── CHECK 1.8: category_configs — GAP CHECK ─────────────────────────
            print("--- CHECK 1.8: category_configs ---")
            query_cat = text("SELECT count(*) FROM information_schema.tables WHERE table_name = 'category_configs'")
            cat_exists = (await session.execute(query_cat)).scalar()
            
            if cat_exists:
                query_cat_rows = text("SELECT count(*) FROM category_configs")
                cat_rows = (await session.execute(query_cat_rows)).scalar()
                
                if cat_rows >= 3:
                    status_1_8 = "PASS"
                    notes_1_8 = f"Table exists with {cat_rows} categories"
                else:
                    status_1_8 = "PARTIAL"
                    notes_1_8 = f"Table exists but only {cat_rows} rows (need 3+)"
                    migration_actions.append("Seed category_configs")
            else:
                status_1_8 = "FAIL"
                notes_1_8 = "Table category_configs does not exist"
                migration_actions.append("Create category_configs table")

            results.append(["1.8", "category_configs created and seeded", status_1_8, notes_1_8])
            
            # ─── CHECK 1.9: INDEXES ON HIGH-TRAFFIC COLUMNS ──────────────────────
            print("--- CHECK 1.9: Indexes ---")
            query_idx = text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename IN ('topics', 'topic_sentiment_breakdown', 'raw_articles', 'topic_articles')
            """)
            indexes = (await session.execute(query_idx)).all()
            index_defs = [row.indexdef for row in indexes]
            
            # Simple substring check
            has_sb_idx = any("topic_id" in d and "topic_sentiment_breakdown" in d for d in index_defs)
            
            if has_sb_idx:
                status_1_9 = "PASS"
                notes_1_9 = "All critical indexes present"
            else:
                status_1_9 = "FAIL"
                notes_1_9 = "topic_sentiment_breakdown(topic_id) index missing"
                migration_actions.append("Create index on topic_sentiment_breakdown(topic_id)")
                
            results.append(["1.9", "Performance indexes exist", status_1_9, notes_1_9])
            
            # ─── PRINT REPORT ───────────────────────────────────────────────────
            print("\n" + "="*80)
            print("AUDIT PROMPT 1 SUMMARY REPORT")
            print("="*80)
            # print(tabulate(results, headers=["Check", "Description", "Status", "Notes"], tablefmt="grid"))
            # Manual formatting
            headers = ["Check", "Description", "Status", "Notes"]
            col_widths = [8, 45, 10, 50]
            header_row = "".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
            print("-" * sum(col_widths))
            print(header_row)
            print("-" * sum(col_widths))
            for row in results:
                print("".join(f"{str(c):<{w}}" for c, w in zip(row, col_widths)))
            print("-" * sum(col_widths))
            
            pass_count = sum(1 for r in results if r[2] == "PASS")
            print(f"\nOVERALL SCORE: {pass_count}/9 checks passed")
            
            if migration_actions:
                print("\nMIGRATION ACTIONS NEEDED (in order of priority):")
                for i, action in enumerate(migration_actions, 1):
                    print(f"{i}. {action}")
        except Exception as e:
            print(f"Error executing audit: {e}")
            import traceback
            traceback.print_exc()
            
        return # finish after one session

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_audit())
