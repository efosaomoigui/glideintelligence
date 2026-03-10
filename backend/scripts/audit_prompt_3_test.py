import asyncio
import sys
import os
import json
from sqlalchemy import text
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db
from app.services.ai.content_generator import AIContentGenerator
from app.models.intelligence import CategoryConfig

async def run_live_test():
    print("Running Audit Prompt 3 Live Test...")
    
    async for session in get_db():
        try:
            # 1. Initialize Generator
            generator = AIContentGenerator(session)
            print("AIContentGenerator initialized.")

            # 2. Mock Data
            topic_id = 999
            title = "CBN Holds Interest Rate at 27.5% Amid Inflation Concerns"
            category = "economic"
            news_content = """
            The Central Bank of Nigeria has maintained its benchmark interest rate
            at 27.5% for the third consecutive month. The Monetary Policy Committee
            cited the need to balance inflation control with economic growth.
            Inflation remains at 34.8% while the Naira has shown stability.
            Banking sector executives welcomed the decision while manufacturers
            expressed concerns about the high cost of credit.
            """
            
            # Create a mock CategoryConfig object (or fetch real one)
            # Fetching real one is better to test DB integration too
            stmt = text("SELECT * FROM category_configs WHERE category = 'economic'")
            result = (await session.execute(stmt)).first()
            
            if not result:
                print("FAIL: 'economic' category config not found in DB.")
                return

            # Construct CategoryConfig object manually or via ORM
            # Since we used raw sql for fetch, let's just make a dummy object compatible with type hinting
            # straightforward way:
            dim_mappings = result.dimension_mappings
            impact_cats = result.impact_categories
            
            class MockConfig:
                category = "economic"
                dimension_mappings = dim_mappings
                impact_categories = impact_cats
            
            config = MockConfig()
            
            print(f"Testing with category: {config.category}")
            print(f"Primary dims: {config.dimension_mappings.get('primary_dimensions')}")

            # 3. Run generate_sentiment_breakdown
            print("\nCalling generate_sentiment_breakdown...")
            start_time = datetime.now()
            result = await generator.generate_sentiment_breakdown(
                topic_title=title,
                articles_text=news_content,
                category_config=config
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"Call completed in {duration:.2f}s")
            print("Result type:", type(result))
            print("Result count:", len(result))
            if len(result) > 0:
                print("First item:", json.dumps(result[0], indent=2))
                print("Has dimension_type:", 'dimension_type' in result[0])
                print("Has sentiment_score:", 'sentiment_score' in result[0])
                print("Score is float:", isinstance(result[0].get('sentiment_score'), (float, int))) # float or int (0.0 could be 0)
            
            # Validate Constraints
            if not isinstance(result, list):
                print("FAIL: Result is not a list")
            elif len(result) < 2:
                print("FAIL: Result has fewer than 2 items")
            else:
                 # Check fields
                 required = {'dimension_type', 'dimension_value', 'sentiment', 'sentiment_score', 'percentage', 'icon', 'description'}
                 missing = required - set(result[0].keys())
                 if missing:
                     print(f"FAIL: Missing fields in first item: {missing}")
                 else:
                     print("SUCCESS: Live test passed validation logic.")

        except Exception as e:
            print(f"\nFAIL: Exception during test: {e}")
            import traceback
            traceback.print_exc()
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_live_test())
