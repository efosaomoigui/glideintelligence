import os
import sys
from dotenv import load_dotenv

# Add parent dir to path to import app modules
sys.path.append(os.getcwd())

load_dotenv()

async def test_gemini():
    from app.services.ai.gemini_service import GeminiService
    
    print("Initializing GeminiService...")
    try:
        service = GeminiService()
        print(f"Service initialized. Model: {service.model_name}")
        
        prompt = "Say 'hello world' if you can hear me."
        print(f"Sending prompt: {prompt}")
        
        response = service.generate_content(prompt)
        print(f"Response: {response}")
        return True
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("This means the 'google-genai' package is likely not installed in this environment.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gemini())
