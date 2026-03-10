import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend dir to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Load .env from backend dir
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal
from app.services.ai.summarization_service import SummarizationService
import logging

# Configure logging to see progress of model downloads
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_ai_pipeline_async():
    print("=== Testing AI Pipeline (Dynamic Dispatch) ===")
    
    sample_text = """
    Nigeria's Central Bank has raised interest rates to combat soaring inflation, which reached 30% last month. 
    The move is expected to stabilize the Naira but may increase the cost of borrowing for businesses. 
    Economists predict a slowdown in the manufacturing sector as a result. 
    Meanwhile, the government is pledging new subsidies to cushion the effect on the poor.
    """
    
    print("\n[Input Text]:", sample_text.strip())
    
    async with AsyncSessionLocal() as db:
        svc = SummarizationService(db)
        try:
            # Helper to fetch active providers
            providers = await svc._get_active_providers()
            print(f"\n[Active Providers]: {[p.name for p in providers]}")

            print("\n--- Running Pipeline ---")
            # Note: Pipeline expects a list of strings
            result = await svc.generate_summary_pipeline([sample_text])
            
            print(f"\n[Result Provider]: {result.get('provider')}")
            print(f"[Confidence]: {result.get('confidence_score')}")
            
            print(f"\n[Summary]: {result.get('summary')}")
            print(f"\n[Sentiment]: {result.get('sentiment')}")
            print(f"\n[Framing]: {result.get('regional_framing')}")
            
        except Exception as e:
            print(f"\n[Error]: Pipeline failed - {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_ai_pipeline_async())
