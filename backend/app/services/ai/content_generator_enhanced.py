from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.intelligence import CategoryConfig
from app.models.settings import AIProvider
import json
import logging
import time
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class RateLimiter:
    """Track and enforce rate limits per provider."""
    
    def __init__(self):
        self.requests = defaultdict(list)  # provider_name -> [timestamp, timestamp, ...]
        self.limits = {
            'gemini': 15,      # 15 requests per minute (free tier)
            'claude': 50,      # 50 requests per minute
            'openai': 60,      # 60 requests per minute
            'ollama': 999      # No limit (local)
        }
    
    async def wait_if_needed(self, provider_name: str):
        """Wait if we've hit the rate limit."""
        limit = self.limits.get(provider_name.lower(), 60)
        now = time.time()
        cutoff = now - 60  # Look at last 60 seconds
        
        # Clean old requests
        self.requests[provider_name] = [
            ts for ts in self.requests[provider_name] if ts > cutoff
        ]
        
        # Check if we're at the limit
        if len(self.requests[provider_name]) >= limit:
            oldest = self.requests[provider_name][0]
            wait_time = 60 - (now - oldest) + 0.5  # Add 0.5s buffer
            if wait_time > 0:
                logger.warning(f"⏱️  Rate limit: waiting {wait_time:.1f}s for {provider_name}")
                await asyncio.sleep(wait_time)
        
        # Record this request
        self.requests[provider_name].append(time.time())


class CostTracker:
    """Track API costs across providers."""
    
    def __init__(self):
        self.costs_by_provider = defaultdict(float)
        self.costs_by_day = defaultdict(float)
        self.topics_processed = 0
        self.tokens_used = 0
        
        # Cost per 1M tokens (input + output averaged)
        self.cost_per_1m_tokens = {
            'gemini': 0.1875,   # (0.075 + 0.30) / 2
            'claude': 1.625,    # Haiku average
            'openai': 0.75,     # GPT-3.5 average
            'ollama': 0.0       # Free
        }
    
    def record_usage(self, provider: str, tokens: int):
        """Record token usage and calculate cost."""
        cost = (tokens / 1_000_000) * self.cost_per_1m_tokens.get(provider.lower(), 0)
        
        self.costs_by_provider[provider] += cost
        today = datetime.now().strftime('%Y-%m-%d')
        self.costs_by_day[today] += cost
        self.tokens_used += tokens
        self.topics_processed += 1
        
        return cost
    
    def get_today_cost(self) -> float:
        """Get total cost today."""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.costs_by_day.get(today, 0.0)
    
    def can_process(self, daily_budget: float) -> bool:
        """Check if we're within budget."""
        return self.get_today_cost() < daily_budget


def safe_encode(text: str) -> str:
    """Fix encoding issues by replacing problematic characters."""
    if not text:
        return ""
    
    try:
        # Try to encode/decode to catch issues
        return text.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        # If that fails, remove non-ASCII
        return ''.join(char if ord(char) < 128 else '?' for char in text)


class AIContentGenerator:
    """
    🚀 ENHANCED: Generate AI analysis with smart features.
    
    New Features:
    - Rate limiting (respects provider quotas)
    - Cost tracking (monitors spend)
    - Encoding fixes (handles special characters)
    - Better error handling
    - Performance metrics
    """
    
    def __init__(self, db: AsyncSession, rate_limiter: RateLimiter = None, cost_tracker: CostTracker = None):
        self.db = db
        self.rate_limiter = rate_limiter or RateLimiter()
        self.cost_tracker = cost_tracker or CostTracker()
        self._tokens_used = 0
        self._provider_used = None
    
    async def _get_enabled_providers(self) -> List[AIProvider]:
        """Fetch enabled AI providers ordered by priority."""
        result = await self.db.execute(
            select(AIProvider)
            .where(AIProvider.enabled == True)
            .order_by(AIProvider.priority.desc())
        )
        return result.scalars().all()
    
    async def _call_ai_provider(
        self,
        provider: AIProvider,
        prompt: str,
        max_tokens: int = 2000,
        timeout_seconds: int = 60
    ) -> str:
        """Call AI provider with rate limiting and timeout."""
        
        # Wait if we're hitting rate limit
        await self.rate_limiter.wait_if_needed(provider.name)
        
        try:
            async def _make_call():
                if provider.name.lower() in ["gemini", "google"]:
                    from app.services.ai.gemini_service import GeminiService
                    service = GeminiService()
                    return service.generate_content(prompt, model=provider.model, max_tokens=max_tokens)
                
                elif provider.name.lower() in ["claude", "anthropic"]:
                    from app.services.ai.claude_service import ClaudeService
                    service = ClaudeService(api_key=provider.api_key)
                    return service.generate_content(prompt, model=provider.model, max_tokens=max_tokens)
                
                elif provider.name.lower() == "openai":
                    from app.services.ai.openai_service import OpenAIService
                    service = OpenAIService(api_key=provider.api_key)
                    return service.generate_content(prompt, model=provider.model, max_tokens=max_tokens)
                
                elif provider.name.lower() == "ollama":
                    from app.services.ai.ollama_service import ollama_service
                    
                    if not ollama_service.is_available():
                        raise Exception("Ollama service is not available")
                    
                    messages = [{"role": "user", "content": prompt}]
                    response = ollama_service.chat(
                        model=provider.model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=max_tokens
                    )
                    return response
                
                elif provider.name.lower() in ["local", "bart", "local (bart)"]:
                    from app.services.ai.local_inference import local_inference
                    summary = local_inference.generate_summary(prompt, max_length=500)
                    return summary
                
                else:
                    raise ValueError(f"Unsupported provider: {provider.name}")
            
            # Execute with timeout
            response = await asyncio.wait_for(_make_call(), timeout=timeout_seconds)
            
            # Fix encoding issues
            response = safe_encode(response)
            
            self._provider_used = provider.name
            self._tokens_used += len(prompt.split()) * 1.3 + len(response.split()) * 1.3
            
            return response
        
        except asyncio.TimeoutError:
            logger.error(f"Provider {provider.name} timed out after {timeout_seconds}s")
            raise Exception(f"Timeout after {timeout_seconds}s")
        
        except Exception as e:
            logger.error(f"Provider {provider.name} failed: {e}")
            raise
    
    def _extract_json(self, content: str) -> str:
        """Extract JSON from content."""
        import re
        
        content = safe_encode(content)  # Fix encoding first
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        content = content.strip()
        
        if not (content.startswith("{") or content.startswith("[")):
            match_array = re.search(r'\[.*\]', content, re.DOTALL)
            match_object = re.search(r'\{.*\}', content, re.DOTALL)
            
            if match_array and match_object:
                content = match_array.group(0) if match_array.start() < match_object.start() else match_object.group(0)
            elif match_array:
                content = match_array.group(0)
            elif match_object:
                content = match_object.group(0)
        
        return content
    
    async def generate_complete_analysis(
        self,
        topic_title: str,
        topic_content: str,
        category_config: CategoryConfig,
        sources: List[Dict],
        timeout_seconds: int = 90,
        daily_budget: float = 5.0
    ) -> Dict:
        """
        🚀 ENHANCED: Generate ALL 4 components in ONE API call.
        
        New Features:
        - Rate limiting
        - Cost tracking
        - Budget enforcement
        - Encoding fixes
        """
        
        # Check budget before processing
        if not self.cost_tracker.can_process(daily_budget):
            raise Exception(f"Daily budget of ${daily_budget:.2f} reached (spent: ${self.cost_tracker.get_today_cost():.2f})")
        
        logger.info(f"🚀 Starting optimized analysis: {topic_title[:60]}...")
        start_time = time.time()
        
        # Fix encoding in inputs
        topic_title = safe_encode(topic_title)
        topic_content = safe_encode(topic_content)
        sources = [
            {k: safe_encode(v) if isinstance(v, str) else v for k, v in s.items()}
            for s in sources
        ]
        
        # Build unified prompt
        prompt = self._build_unified_prompt(
            topic_title,
            category_config.category,
            topic_content,
            sources,
            category_config
        )
        
        # Try providers with fallback
        providers = await self._get_enabled_providers()
        
        if not providers:
            raise Exception("No enabled AI providers")
        
        last_error = None
        
        for provider in providers:
            try:
                logger.info(f"Attempting with {provider.name} (priority: {provider.priority})")
                
                content = await self._call_ai_provider(
                    provider, 
                    prompt, 
                    max_tokens=4000,
                    timeout_seconds=timeout_seconds
                )
                
                # Parse JSON
                extracted = self._extract_json(content)
                result = json.loads(extracted)
                
                # Validate structure
                required_keys = ['sentiment_breakdown', 'source_perspectives', 'regional_impacts', 'intelligence_card']
                missing = [k for k in required_keys if k not in result]
                
                if missing:
                    raise ValueError(f"Missing keys: {missing}")
                
                if len(result['sentiment_breakdown']) < 2:
                    raise ValueError("sentiment_breakdown has < 2 items")
                
                if len(result['regional_impacts']) < 2:
                    raise ValueError("regional_impacts has < 2 items")
                
                # Fix encoding in results
                result = self._fix_encoding_in_result(result)
                
                # Track cost
                cost = self.cost_tracker.record_usage(provider.name, int(self._tokens_used))
                
                # Add metadata
                result['provider_used'] = provider.name
                result['tokens_used'] = int(self._tokens_used)
                result['cost_estimate'] = cost
                
                duration = time.time() - start_time
                
                logger.info(f"✅ Analysis complete: {provider.name}, {int(self._tokens_used)} tokens, ${cost:.4f}, {duration:.2f}s")
                logger.info(f"📊 Today's spend: ${self.cost_tracker.get_today_cost():.4f} / ${daily_budget:.2f}")
                
                return result
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                last_error = e
                continue
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Provider {provider.name} failed: {error_msg}")
                
                if '429' in error_msg or 'quota' in error_msg.lower():
                    logger.warning(f"⚠️  {provider.name} hit quota - trying next provider")
                
                last_error = e
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    def _fix_encoding_in_result(self, result: Dict) -> Dict:
        """Fix encoding in all string values in result."""
        
        def fix_value(val):
            if isinstance(val, str):
                return safe_encode(val)
            elif isinstance(val, dict):
                return {k: fix_value(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [fix_value(item) for item in val]
            return val
        
        return fix_value(result)
    
    def _build_unified_prompt(
        self,
        topic_title: str,
        category: str,
        topic_content: str,
        sources: List[Dict],
        category_config: CategoryConfig
    ) -> str:
        """Build unified prompt (same as before)."""
        
        # Format dimensions
        dimension_list = []
        dimensions = category_config.dimension_mappings.get("primary_dimensions", [])
        for dim_type in dimensions:
            options_key = f"{dim_type}_options"
            if options_key in category_config.dimension_mappings:
                options = category_config.dimension_mappings[options_key][:8]
                dimension_list.append(f"{dim_type}: {', '.join(options)}")
        
        # Format sources
        sources_text = "\n".join([
            f"SOURCE {i+1}: {s.get('name', 'Unknown')} ({s.get('type', 'unknown')})\n{s.get('headline', '')}"
            for i, s in enumerate(sources[:5])
        ])
        
        # Format impact categories
        impact_categories = category_config.impact_categories
        impact_text = "\n".join([
            f"- {cat.get('key')}: {cat.get('label')} {cat.get('icon')}"
            for cat in impact_categories[:6]
        ])
        
        prompt = f"""You are analyzing a {category} news topic for an intelligence platform.

═══════════════════════════════════════════════════════════════
TOPIC INFORMATION
═══════════════════════════════════════════════════════════════
Title: "{topic_title}"
Category: {category}

News Content:
{topic_content[:1800]}...

Sources:
{sources_text}

═══════════════════════════════════════════════════════════════
YOUR TASK: Generate COMPLETE INTELLIGENCE ANALYSIS
═══════════════════════════════════════════════════════════════

You must provide ALL FOUR components below in a single JSON response.

COMPONENT 1 — SENTIMENT BREAKDOWN
Analyze sentiment across these {category}-specific dimensions:
{chr(10).join(dimension_list)}

For EACH dimension type, select 2-3 most relevant values and provide:
- sentiment: "positive", "negative", "neutral", or "mixed"
- sentiment_score: Float from -1.0 to +1.0
- percentage: Coverage % (should roughly sum to 100% per dimension type)
- icon: Appropriate emoji
- description: One sentence (max 120 chars)

COMPONENT 2 — SOURCE PERSPECTIVES
For each source above, determine:
- frame_label: 2-4 word framing angle (e.g., "Economic Optimism")
- sentiment: Overall sentiment of their framing
- sentiment_percentage: Deviation from neutral (e.g., "+48%", "-23%")
- key_narrative: One sentence capturing their angle (max 120 chars)

COMPONENT 3 — REGIONAL IMPACTS
Select 3-4 most relevant impact categories from:
{impact_text}

For each, provide:
- impact_category: The key from the list above
- icon: The emoji from the list
- title: The label from the list
- value: SPECIFIC, CONCRETE impact (MUST use numbers/amounts/timeframes)
- severity: "low", "medium", "high", or "critical"
- context: Why this matters (max 150 chars)

CRITICAL: Values must be CONCRETE and use only ASCII-compatible characters.

COMPONENT 4 — INTELLIGENCE CARD
Create a homepage card with:
- category: "{category}"
- icon: Appropriate emoji
- title: 3-6 words, punchy
- description: One sentence (max 15 words)
- trend_percentage: Estimate (e.g., "+12%")
- is_positive: true or false

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════

Return ONLY valid JSON (no markdown, no extra text):

{{
  "sentiment_breakdown": [...],
  "source_perspectives": [...],
  "regional_impacts": [...],
  "intelligence_card": {{...}}
}}"""

        return safe_encode(prompt)
