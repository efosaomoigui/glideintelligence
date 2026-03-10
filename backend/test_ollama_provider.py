"""
Test Ollama Provider Integration
"""
import asyncio
import sys
from app.database import AsyncSessionLocal
from app.models.settings import AIProvider
from app.services.ai.ollama_service import ollama_service
from app.services.ai.content_generator import AIContentGenerator
from sqlalchemy import select

async def test_ollama():
    print("="*60)
    print("Ollama Provider Integration Test")
    print("="*60)
    
    # 1. Check Ollama service availability
    print("\n1. Checking Ollama service...")
    if ollama_service.is_available():
        print("   [OK] Ollama service is running")
    else:
        print("   [ERROR] Ollama service is not available")
        print("   Make sure Docker container is running:")
        print("   docker-compose up -d ollama")
        return False
    
    # 2. List available models
    print("\n2. Checking available models...")
    models = ollama_service.list_models()
    if models:
        print(f"   [OK] Found {len(models)} model(s):")
        for model in models:
            print(f"      - {model.get('name', 'unknown')}")
    else:
        print("   [WARNING] No models found")
        print("   Pull a model with:")
        print("   docker exec -it ollama ollama pull llama3.2:3b-instruct")
        return False
    
    # 3. Test basic generation
    print("\n3. Testing basic text generation...")
    try:
        response = ollama_service.generate(
            model="llama3.2:3b-instruct",
            prompt="Explain what artificial intelligence is in one sentence.",
            max_tokens=100
        )
        print(f"   [OK] Generation successful")
        print(f"   Response: {response[:200]}...")
    except Exception as e:
        print(f"   [ERROR] Generation failed: {e}")
        return False
    
    # 4. Test structured output (JSON)
    print("\n4. Testing structured output (JSON)...")
    prompt = """Generate a JSON object with sentiment analysis for this text:
"The economy is showing signs of recovery with GDP growth at 3.5%"

Return ONLY valid JSON in this format:
{
  "sentiment": "positive",
  "score": 0.8,
  "summary": "brief summary"
}"""
    
    try:
        response = ollama_service.generate(
            model="llama3.2:3b-instruct",
            prompt=prompt,
            temperature=0.3,
            max_tokens=200
        )
        print(f"   [OK] Structured generation successful")
        print(f"   Response:\n{response}")
    except Exception as e:
        print(f"   [ERROR] Structured generation failed: {e}")
        return False
    
    # 5. Test with AIContentGenerator
    print("\n5. Testing with AIContentGenerator...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AIProvider).where(AIProvider.name == "Ollama")
        )
        ollama_provider = result.scalar_one_or_none()
        
        if not ollama_provider:
            print("   [ERROR] Ollama provider not found in database")
            print("   Run: python seed_ollama_provider.py")
            return False
        
        if not ollama_provider.enabled:
            print("   [WARNING] Ollama provider is disabled")
            print("   Enable it in admin UI or database")
            return False
        
        print(f"   [OK] Ollama provider found (Priority: {ollama_provider.priority})")
        
        # Test via content generator
        generator = AIContentGenerator(db)
        try:
            test_prompt = "Summarize: The stock market reached new highs today."
            response = await generator._call_ai_provider(
                ollama_provider,
                test_prompt,
                max_tokens=100
            )
            print(f"   [OK] Content generator integration successful")
            print(f"   Response: {response[:200]}...")
        except Exception as e:
            print(f"   [ERROR] Content generator failed: {e}")
            return False
    
    # 6. Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("[OK] Ollama service is running")
    print("[OK] Models are available")
    print("[OK] Basic generation works")
    print("[OK] Structured output works")
    print("[OK] Content generator integration works")
    print("\n[SUCCESS] All tests passed!")
    print("\nOllama is ready to use as fallback AI provider.")
    print("="*60)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_ollama())
    sys.exit(0 if result else 1)
