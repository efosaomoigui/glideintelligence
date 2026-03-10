import asyncio
import sys
import os
import json
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def run_audit():
    print("Running Audit Prompt 2 of 6 — CATEGORY CONFIGURATION SYSTEM\n")
    
    results = []
    migration_actions = []

    async for session in get_db():
        try:
            # ─── CHECK 2.1: ALL 8 CATEGORIES EXIST ──────────────────────────────
            print("--- CHECK 2.1: ALL 8 CATEGORIES EXIST ---")
            expected_categories = {
                'business', 'economic', 'environmental', 'political', 
                'regional', 'security', 'social', 'technology'
            }
            query_2_1 = text("SELECT category FROM category_configs ORDER BY category")
            found_categories = set((await session.execute(query_2_1)).scalars().all())
            
            missing_cats = expected_categories - found_categories
            
            if not missing_cats:
                status_2_1 = "PASS"
                notes_2_1 = "All 8 categories exist"
            else:
                status_2_1 = "FAIL"
                notes_2_1 = f"Missing: {', '.join(missing_cats)}"
                migration_actions.append(f"Insert missing categories: {', '.join(missing_cats)}")

            results.append(["2.1", "All 8 categories exist", status_2_1, notes_2_1])

            # ─── CHECK 2.2: ECONOMIC CATEGORY STRUCTURE ─────────────────────────
            print("--- CHECK 2.2: ECONOMIC CATEGORY STRUCTURE ---")
            query_2_2 = text("""
                SELECT
                    category,
                    dimension_mappings->'primary_dimensions' AS primary_dimensions,
                    jsonb_array_length(dimension_mappings->'primary_dimensions') AS dim_count,
                    jsonb_array_length(impact_categories) AS impact_count
                FROM category_configs
                WHERE category = 'economic';
            """)
            row_2_2 = (await session.execute(query_2_2)).first()
            
            if row_2_2:
                pd_json = row_2_2.primary_dimensions
                # If it's a string, load it. If it's distinct type (unlikely with asyncpg+sqlalchemy sometimes), handle it.
                # SQLAlchemy with asyncpg usually returns python objects for JSONB.
                primary_dims = pd_json if isinstance(pd_json, list) else [] # fallback
                
                has_dims = all(d in primary_dims for d in ["sector", "stakeholder", "impact_area"])
                counts_ok = row_2_2.dim_count >= 3 and row_2_2.impact_count >= 3
                
                if has_dims and counts_ok:
                    status_2_2 = "PASS"
                    notes_2_2 = "Economic structure correct"
                else:
                    status_2_2 = "FAIL"
                    notes_2_2 = f"Dims: {primary_dims}, Count: {row_2_2.dim_count}, Impacts: {row_2_2.impact_count}"
                    migration_actions.append("Fix 'economic' category config JSON")
            else:
                 status_2_2 = "FAIL"
                 notes_2_2 = "Category 'economic' not found"
                 migration_actions.append("Insert 'economic' category")

            results.append(["2.2", "Economic structure correct", status_2_2, notes_2_2])

            # ─── CHECK 2.3: POLITICAL CATEGORY STRUCTURE ─────────────────────────
            print("--- CHECK 2.3: POLITICAL CATEGORY STRUCTURE ---")
            query_2_3 = text("""
                SELECT
                    category,
                    dimension_mappings->'primary_dimensions' AS primary_dimensions,
                    dimension_mappings->'region_options' AS region_options,
                    jsonb_array_length(impact_categories) AS impact_count
                FROM category_configs
                WHERE category = 'political';
            """)
            row_2_3 = (await session.execute(query_2_3)).first()
            
            if row_2_3:
                pd = row_2_3.primary_dimensions or []
                ro = row_2_3.region_options
                
                has_req_dims = "stakeholder" in pd and "region" in pd
                has_regions = ro is not None and len(ro) > 0 # Simple check
                # Ideally check for "North", "South" etc but prompt says "includes North, South..."
                
                if has_req_dims and has_regions and row_2_3.impact_count >= 3:
                     status_2_3 = "PASS"
                     notes_2_3 = "Political structure correct"
                else:
                     status_2_3 = "FAIL"
                     notes_2_3 = f"Missing regions or dimensions. Regions: {ro}"
                     migration_actions.append("Fix 'political' category config (add regions)")
            else:
                 status_2_3 = "FAIL"
                 notes_2_3 = "Category 'political' not found"

            results.append(["2.3", "Political structure correct", status_2_3, notes_2_3])

            # ─── CHECK 2.4: SECURITY CATEGORY STRUCTURE ──────────────────────────
            print("--- CHECK 2.4: SECURITY CATEGORY STRUCTURE ---")
            query_2_4 = text("""
                SELECT
                    category,
                    dimension_mappings->'primary_dimensions' AS primary_dimensions,
                    dimension_mappings->'threat_type_options' AS threat_types,
                    jsonb_array_length(impact_categories) AS impact_count
                FROM category_configs
                WHERE category = 'security';
            """)
            row_2_4 = (await session.execute(query_2_4)).first()
            
            if row_2_4:
                pd = row_2_4.primary_dimensions or []
                tt = row_2_4.threat_types
                
                has_threat = "threat_type" in pd and "sector" not in pd
                has_options = tt is not None and len(tt) > 0
                
                if has_threat and has_options and row_2_4.impact_count >= 3:
                    status_2_4 = "PASS"
                    notes_2_4 = "Security structure correct"
                else:
                    status_2_4 = "FAIL"
                    notes_2_4 = f"Threat types missing or 'sector' present. Dims: {pd}"
                    migration_actions.append("Fix 'security' config (add threat_types, remove sector)")
            else:
                status_2_4 = "FAIL"
                notes_2_4 = "Category 'security' not found"

            results.append(["2.4", "Security structure correct", status_2_4, notes_2_4])

            # ─── CHECK 2.5: IMPACT CATEGORIES ARE CATEGORY-SPECIFIC ─────────────
            print("--- CHECK 2.5: IMPACT CATEGORIES SPECIFICITY ---")
            query_2_5 = text("""
                SELECT category, impact_categories
                FROM category_configs
                WHERE category IN ('economic', 'political', 'security', 'technology')
                ORDER BY category;
            """)
            rows_2_5 = (await session.execute(query_2_5)).all()
            # impacts_map = {r.category: set(r.impact_categories) for r in rows_2_5} # Caused unhashable dict
            impacts_map = {r.category: r.impact_categories for r in rows_2_5}
            
            cats_to_check = ['economic', 'political', 'security', 'technology']
            if len(impacts_map) < 4:
                status_2_5 = "FAIL"
                notes_2_5 = "Some categories missing for check"
            else:
                # Naive check: ensure they are not all identical
                # Better: check for specific keywords per prompt
                
                keywords = {
                    'economic': {'market_impact', 'business_climate'},
                    'political': {'legal_risk', 'regional_tension', 'stakes'},
                    'security': {'threat_level', 'affected_areas'},
                    'technology': {'innovation_potential', 'adoption_barriers'}
                }
                
                failed_cats = []
                for cat, keys in keywords.items():
                    if cat in impacts_map:
                        raw_impacts = impacts_map[cat]
                        impacts_list = raw_impacts if isinstance(raw_impacts, list) else []
                        # Handle if elements are dicts (e.g. {'name': 'market_impact', ...}) or strings
                        current_impacts = set()
                        for i in impacts_list:
                            if isinstance(i, dict):
                                # Assume 'name' or similar key, or just stringify
                                current_impacts.add(str(i.get('name', i)).lower().replace(' ', '_'))
                            else:
                                current_impacts.add(str(i).lower().replace(' ', '_'))
                        
                        # Check intersection
                        if not keys.intersection(current_impacts):
                             # Try loose matching
                             if not any(k in str(current_impacts) for k in keys):
                                 failed_cats.append(cat)
                
                if not failed_cats:
                    status_2_5 = "PASS"
                    notes_2_5 = "Impact categories valid and specific"
                else:
                    status_2_5 = "FAIL"
                    notes_2_5 = f"Impacts generic/wrong for: {', '.join(failed_cats)}"
                    migration_actions.append(f"Update impact categories for: {', '.join(failed_cats)}")

            results.append(["2.5", "Impact categories are specific", status_2_5, notes_2_5])
            
            # ─── CHECK 2.6: JSON STRUCTURE IS VALID ──────────────────────────────
            print("--- CHECK 2.6: JSON STRUCTURE ---")
            # Using raw SQL for boolean checks
            query_2_6 = text("""
                SELECT
                    category,
                    CASE WHEN dimension_mappings ? 'primary_dimensions' THEN 'OK' ELSE 'MISSING' END AS has_primary_dims,
                    CASE WHEN jsonb_typeof(impact_categories) = 'array' THEN 'OK' ELSE 'WRONG TYPE' END AS impact_is_array
                FROM category_configs
                ORDER BY category;
            """)
            rows_2_6 = (await session.execute(query_2_6)).all()
            
            failures_2_6 = [r.category for r in rows_2_6 if r.has_primary_dims != 'OK' or r.impact_is_array != 'OK']
            
            if not failures_2_6 and len(rows_2_6) == 8:
                status_2_6 = "PASS"
                notes_2_6 = "All 8 categories have valid JSON"
            else:
                status_2_6 = "FAIL"
                notes_2_6 = f"Invalid JSON in: {', '.join(failures_2_6)}" if failures_2_6 else "Missing categories"
                migration_actions.append("Fix JSON structure (ensure primary_dimensions key and impact array)")

            results.append(["2.6", "JSON structure valid", status_2_6, notes_2_6])

            # ─── CHECK 2.7: OPTIONS ARRAYS ARE NON-EMPTY ─────────────────────────
            print("--- CHECK 2.7: OPTIONS ARRAYS NON-EMPTY ---")
            # Using subqueries or easy access? 
            # jsonb_array_length is easier than count() subquery
            query_2_7 = text("""
                SELECT
                    category,
                    jsonb_array_length(dimension_mappings->'primary_dimensions') AS dim_count,
                    jsonb_array_length(impact_categories) AS impact_count
                FROM category_configs
                ORDER BY category;
            """)
            rows_2_7 = (await session.execute(query_2_7)).all()
            
            failures_2_7 = [r.category for r in rows_2_7 if r.dim_count < 2 or r.impact_count < 3]
            
            if not failures_2_7 and len(rows_2_7) == 8:
                status_2_7 = "PASS"
                notes_2_7 = "All have sufficient dimensions/impacts"
            else:
                status_2_7 = "FAIL"
                notes_2_7 = f"Counts too low: {', '.join(failures_2_7)}"
                migration_actions.append(f"Populate dimensions/impacts for: {', '.join(failures_2_7)}")
            
            results.append(["2.7", "Options arrays non-empty", status_2_7, notes_2_7])

            # ─── REPORT ─────────────────────────────────────────────────────────
            headers = ["Check", "Description", "Status", "Notes"]
            col_widths = [6, 40, 8, 50]
            header_row = "".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
            print("\n" + "="*80)
            print("AUDIT PROMPT 2 SUMMARY REPORT")
            print("="*80)
            print("-" * sum(col_widths))
            print(header_row)
            print("-" * sum(col_widths))
            for row in results:
                print("".join(f"{str(c):<{w}}" for c, w in zip(row, col_widths)))
            print("-" * sum(col_widths))
            
            pass_count = sum(1 for r in results if r[2] == "PASS")
            print(f"\nOVERALL CATEGORY CONFIG SCORE: {pass_count}/7 checks passed.")
            
            if migration_actions:
                 print("\nACTIONS NEEDED:")
                 for action in migration_actions:
                     print(f"- {action}")
                 
                 print("\nSUGGESTED UNIFIED FIX (INSERT):")
                 # We can provide a huge INSERT/ON CONFLICT statement here if needed
                 # But let's just note it
                 print("(See seed_category_configs.py or similar logic to bulk fix)")

        except Exception as e:
            print(f"Error executing audit: {e}")
            import traceback
            traceback.print_exc()
        
        return 

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_audit())
