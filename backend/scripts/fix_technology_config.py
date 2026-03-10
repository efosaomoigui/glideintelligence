import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import get_db

async def fix_technology_config():
    print("Fixing 'technology' category configuration...")
    async for session in get_db():
        try:
            # Update impact_categories for technology
            # Expected: innovation_potential, adoption_barriers, digital_divide
            # We will overwrite the impact_categories array.
            
            stmt = text("""
                UPDATE category_configs
                SET impact_categories = '["innovation_potential", "adoption_barriers", "digital_divide", "market_disruption", "ethical_concerns"]'::jsonb
                WHERE category = 'technology';
            """)
            await session.execute(stmt)
            await session.commit()
            print("Successfully updated 'technology' category impacts.")
            
        except Exception as e:
            print(f"Error fixing technology config: {e}")
            await session.rollback()
        return

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(fix_technology_config())
