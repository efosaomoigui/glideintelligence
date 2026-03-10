import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies BEFORE importing services
sys.modules['anthropic'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

from app.services.ai.content_generator import AIContentGenerator
from app.models.settings import AIProvider
import app.services.ai.gemini_service
import app.services.ai.claude_service
import app.services.ai.openai_service

async def test_ai_providers():
    print("Testing AI Provider Integration...")
    
    # Mock database session
    mock_db = MagicMock()
    generator = AIContentGenerator(mock_db)
    
    # Test cases
    providers = [
        AIProvider(name="Gemini", api_key="test_key", model="gemini-2.0-flash", enabled=True, priority=10),
        AIProvider(name="Claude", api_key="test_key", model="claude-3-sonnet", enabled=True, priority=9),
        AIProvider(name="OpenAI", api_key="test_key", model="gpt-4", enabled=True, priority=8),
    ]
    
    prompt = "Test prompt"
    
    # 1. Test Gemini
    print("\n1. Testing Gemini Provider...")
    # We need to mock the service class where it is IMPORTED in content_generator, 
    # OR mock the class in the module if content_generator imports it from there.
    # content_generator does: from app.services.ai.gemini_service import GeminiService
    
    with patch('app.services.ai.gemini_service.GeminiService') as MockGemini:
        mock_instance = MockGemini.return_value
        mock_instance.generate_content.return_value = "Gemini Response"
        
        response = await generator._call_ai_provider(providers[0], prompt)
        print(f"   Response: {response}")
        assert response == "Gemini Response"
        mock_instance.generate_content.assert_called_once()
        print("   [OK] Validated")

    # 2. Test Claude
    print("\n2. Testing Claude Provider...")
    with patch('app.services.ai.claude_service.ClaudeService') as MockClaude:
        mock_instance = MockClaude.return_value
        mock_instance.generate_content.return_value = "Claude Response"
        
        response = await generator._call_ai_provider(providers[1], prompt)
        print(f"   Response: {response}")
        assert response == "Claude Response"
        mock_instance.generate_content.assert_called_once()
        print("   [OK] Validated")

    # 3. Test OpenAI
    print("\n3. Testing OpenAI Provider...")
    with patch('app.services.ai.openai_service.OpenAIService') as MockOpenAI:
        mock_instance = MockOpenAI.return_value
        mock_instance.generate_content.return_value = "OpenAI Response"
        
        response = await generator._call_ai_provider(providers[2], prompt)
        print(f"   Response: {response}")
        assert response == "OpenAI Response"
        mock_instance.generate_content.assert_called_once()
        print("   [OK] Validated")

if __name__ == "__main__":
    try:
        asyncio.run(test_ai_providers())
        print("\nAll AI provider tests passed successfully!")
    except Exception as e:
        print(f"\n[FAIL] Tests failed: {e}")
        import traceback
        traceback.print_exc()
