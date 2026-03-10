import asyncio
import json
import logging
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai.content_generator import AIContentGenerator, RateLimiter, CostTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_split_prompt_flow():
    """Test that generate_complete_analysis correctly chains two AI calls."""
    
    # Mock dependencies
    db = AsyncMock()
    rate_limiter = MagicMock(spec=RateLimiter)
    cost_tracker = MagicMock(spec=CostTracker)
    cost_tracker.can_process.return_value = True
    cost_tracker.record_usage.return_value = 0.01
    
    generator = AIContentGenerator(db, rate_limiter, cost_tracker)
    
    # Mock Stage 1 Response
    stage1_json = {
        "sentiment_breakdown": [{"dimension_type": "audience", "dimension_value": "local", "sentiment": "positive", "sentiment_score": 0.8, "percentage": 100, "icon": "👍", "description": "Great news!"}],
        "source_perspectives": [{"source_name": "Test News", "source_type": "rss", "frame_label": "Positive", "sentiment": "positive", "sentiment_percentage": "+80%", "key_narrative": "Everything is fine."}],
        "regional_impacts": [{"impact_category": "economy", "icon": "💰", "title": "Economic Boost", "value": "$1B", "severity": "high", "context": "Inflation down."}],
        "verified_category": "business"
    }
    
    # Mock Stage 2 Response
    stage2_json = {
        "intelligence_card": {"category": "business", "icon": "🏢", "title": "Big Biz", "description": "Business is booming.", "trend_percentage": "+5%", "is_positive": True},
        "poll": {"question": "Are you bullish?", "options": ["Yes", "No", "Maybe", "Ask later"]}
    }
    
    # Mock _get_enabled_providers
    mock_provider = MagicMock()
    mock_provider.name = "mock_ai"
    mock_provider.model = "gpt-4"
    generator._get_enabled_providers = AsyncMock(return_value=[mock_provider])
    
    # Mock _call_ai_provider to return different things for each call
    call_count = 0
    async def mock_call_ai(provider, prompt, **kwargs):
        nonlocal call_count
        call_count += 1
        if "STRICT valid JSON" in prompt and "SENTIMENT BREAKDOWN" in prompt.upper():
            return json.dumps(stage1_json)
        elif "STRICT valid JSON" in prompt and "INTELLIGENCE CARD" in prompt.upper():
            return json.dumps(stage2_json)
        return "{}"

    generator._call_ai_provider = mock_call_ai
    
    # Run analysis
    topic_title = "Tech Boom 2026"
    topic_content = "Venture capital is flowing into AI startups at record levels."
    category_config = MagicMock()
    category_config.category = "technology"
    category_config.dimension_mappings = {"primary_dimensions": []}
    category_config.impact_categories = []
    
    sources = [{"name": "Global Tech", "headline": "AI Funding Spikes", "type": "rss"}]
    
    result = await generator.generate_complete_analysis(
        topic_title=topic_title,
        topic_content=topic_content,
        category_config=category_config,
        sources=sources,
        topic_summary="Summary of tech boom.",
        topic_id=1
    )
    
    # Assertions
    print("\n--- TEST RESULTS ---")
    print(f"Call Count: {call_count}")
    print(f"Result Keys: {list(result.keys())}")
    
    assert call_count == 2, f"Expected 2 AI calls, got {call_count}"
    assert result["verified_category"] == "business"
    assert "intelligence_card" in result
    assert "poll" in result
    assert result["sentiment_breakdown"][0]["dimension_value"] == "local"
    
    print("TEST PASSED: Split prompt pipeline working correctly!")

if __name__ == "__main__":
    asyncio.run(test_split_prompt_flow())
