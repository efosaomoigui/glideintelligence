from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.intelligence import CategoryConfig
from app.models.settings import AIProvider
from app.models.ai_usage import AIUsageLog
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
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
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
        
        last_exception = None
        for attempt in range(3):
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
                prompt_words = len(prompt.split())
                resp_words = len(response.split())
                tokens = int(prompt_words * 1.3 + resp_words * 1.3)
                self._tokens_used += tokens
                
                logger.debug(f"Token calculation: {prompt_words} prompt words + {resp_words} response words -> {tokens} tokens")
                return response
                
            except (asyncio.TimeoutError, Exception) as e:
                last_exception = e
                wait_time = (attempt + 1) * 2
                logger.warning(f"⚠️  Attempt {attempt + 1} failed for {provider.name}: {e}. Retrying in {wait_time}s...")
                if attempt < 2:
                    await asyncio.sleep(wait_time)
                
        raise last_exception

    
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
        topic_summary: str = "",
        timeout_seconds: int = 90,
        daily_budget: float = 5.0,
        topic_id: Optional[int] = None
    ) -> Dict:
        """
        🚀 ENHANCED: Generate analysis in TWO stages for better focus and cost.
        
        Stage 1: Intelligence Analysis (Sentiment, Sources, Impact, Verification)
        Stage 2: Engagement Elements (Intelligence Card, Contextual Poll)
        """
        
        # Check budget before processing
        if not self.cost_tracker.can_process(daily_budget):
            raise Exception(f"Daily budget of ${daily_budget:.2f} reached (spent: ${self.cost_tracker.get_today_cost():.2f})")
        
        logger.info(f"🚀 Starting two-stage analysis: {topic_title[:60]}...")
        start_time = time.time()
        
        # Fix encoding in inputs
        topic_title = safe_encode(topic_title)
        topic_content = safe_encode(topic_content)
        topic_summary = safe_encode(topic_summary or topic_content[:500])
        sources = [
            {k: safe_encode(v) if isinstance(v, str) else v for k, v in s.items()}
            for s in sources
        ]
        
        # --- STAGE 1: INTELLIGENCE ANALYSIS ---
        prompt1 = self._build_stage1_prompt(
            topic_title,
            category_config.category,
            topic_summary,
            sources,
            category_config
        )
        
        providers = await self._get_enabled_providers()
        if not providers:
            raise Exception("No enabled AI providers")
        
        last_error = None
        result1 = None
        provider1 = None
        
        for provider in providers:
            try:
                logger.info(f"Stage 1 Attempt with {provider.name}")
                content1 = await self._call_ai_provider(provider, prompt1, max_tokens=2500, timeout_seconds=timeout_seconds)
                extracted1 = self._extract_json(content1)
                result1 = json.loads(extracted1)
                
                # Basic validation for Stage 1
                required_keys1 = ['sentiment_breakdown', 'source_perspectives', 'regional_impacts', 'regional_categories', 'verified_category', 'key_takeaways', 'core_drivers']
                if all(k in result1 for k in required_keys1):
                    provider1 = provider
                    break
                else:
                    logger.warning(f"Stage 1 missing keys from {provider.name}")
            except Exception as e:
                logger.error(f"Stage 1 failed with {provider.name}: {e}")
                last_error = e
                continue
        
        if not result1:
            raise Exception(f"Stage 1 failed for all providers. Last error: {last_error}")

        # --- STAGE 2: ENGAGEMENT ELEMENTS ---
        prompt2 = self._build_stage2_prompt(
            topic_title,
            category_config.category,
            topic_summary,
            json.dumps(result1, indent=2)
        )
        
        result2 = None
        provider2 = None
        
        # Reuse the successful provider from Stage 1 if possible, otherwise fallback
        stage2_providers = [provider1] + [p for p in providers if p.name != provider1.name]
        
        for provider in stage2_providers:
            try:
                logger.info(f"Stage 2 Attempt with {provider.name}")
                content2 = await self._call_ai_provider(provider, prompt2, max_tokens=1500, timeout_seconds=timeout_seconds)
                extracted2 = self._extract_json(content2)
                result2 = json.loads(extracted2)
                
                # Basic validation for Stage 2
                required_keys2 = ['intelligence_card', 'poll']
                if all(k in result2 for k in required_keys2):
                    provider2 = provider
                    break
            except Exception as e:
                logger.error(f"Stage 2 failed with {provider.name}: {e}")
                continue
        
        if not result2:
            logger.warning("Stage 2 failed completely. Using default engagement elements.")
            result2 = {
                "intelligence_card": {
                    "category": category_config.category,
                    "icon": "📊",
                    "title": topic_title[:30],
                    "description": "Analysis generated with partial focus.",
                    "trend_percentage": "0%",
                    "is_positive": True
                },
                "poll": {
                    "question": f"What is your take on {topic_title[:40]}?",
                    "options": ["Supportive", "Concerned", "Needs more info", "No opinion"]
                }
            }

        # --- MERGE RESULTS ---
        final_result = {**result1, **result2}
        final_result = self._fix_encoding_in_result(final_result)
        
        # Track total usage (estimated tokens accumulated in self._tokens_used)
        cost = self.cost_tracker.record_usage(provider1.name, int(self._tokens_used))
        
        # Metadata
        final_result['provider_used'] = f"{provider1.name} + {provider2.name if provider2 else 'default'}"
        final_result['tokens_used'] = int(self._tokens_used)
        final_result['cost_estimate'] = cost
        
        # PERSIST USAGE LOG
        try:
            usage_log = AIUsageLog(
                provider_name=provider1.name,
                model_name=provider1.model,
                tokens_used=int(self._tokens_used),
                cost_usd=cost,
                topic_id=topic_id
            )
            self.db.add(usage_log)
            # await self.db.commit() # Let the caller commit for streaming storage
        except Exception as e:
            logger.error(f"Failed to save AI usage log: {e}")
        
        duration = time.time() - start_time
        logger.info(f"✅ Multi-stage analysis complete: {int(self._tokens_used)} tokens, ${cost:.4f}, {duration:.2f}s")
        
        return final_result

    
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
    
    def _build_stage1_prompt(
        self,
        topic_title: str,
        category: str,
        topic_summary: str,
        sources: List[Dict],
        category_config: CategoryConfig
    ) -> str:
        """Build Stage 1: Intelligence Analysis prompt."""
        
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

        prompt = f"""You are an intelligence analyst for a global news intelligence platform.

Your job is to analyze a news topic and produce structured intelligence insights.

════════════════════════
TOPIC INFORMATION
════════════════════════

title: "{topic_title}"
category: "{category}"

news_summary:
{topic_summary[:2000]}

sources:
{sources_text}

sentiment_dimensions:
{chr(10).join(dimension_list)}

impact_categories:
{impact_text}

════════════════════════
ANALYSIS TASKS
════════════════════════

Perform the following analysis.

1. SENTIMENT BREAKDOWN
Analyze sentiment across the provided sentiment_dimensions.
Each object must contain:
- dimension_type
- dimension_value
- sentiment ("positive","negative","neutral","mixed")
- sentiment_score (float from -1.0 to +1.0)
- percentage (values should roughly sum to 100 per dimension_type)
- icon (emoji)
- description (max 120 characters)

2. SOURCE PERSPECTIVES
Analyze ONLY the 5 most relevant sources.
For each source provide:
- source_name
- source_type ("rss","api","website","social")
- frame_label (2-4 words)
- sentiment ("positive","negative","neutral","mixed")
- sentiment_percentage (deviation from neutral such as "+32%" or "-18%")
- key_narrative (max 120 characters)

3. REGIONAL IMPACTS
Select the 3–4 most relevant impact categories from impact_categories.
For each impact provide:
- impact_category
- icon
- title
- value (must include specific numbers, amounts, or timeframes)
- context (max 150 characters)
Use only ASCII characters.

4. REGIONAL CATEGORIZATION
Tag the topic with 3–5 most relevant regions from the provided hierarchy (Global, Africa, West Africa, etc.).
For each region provide:
- region (canonical name)
- impact ("Positive", "Negative", "Neutral")

5. CATEGORY VERIFICATION
Verify whether the assigned category is correct.
Return the most accurate category strictly from:
"politics", "business", "economy", "technology", "sports", "security", "social", "regional", "environment", "general"

5. KEY TAKEAWAYS
Provide exactly 1 concise key takeaway from the story (max 25 words).

6. CORE DRIVERS
List exactly 2-3 short bullet points (max 15 words each) explaining what is driving or causing this story.

════════════════════════
OUTPUT RULES
════════════════════════
Return STRICT valid JSON only.
Do not include explanations, comments, or markdown.

════════════════════════
OUTPUT FORMAT
════════════════════════
{{
 "sentiment_breakdown": [],
 "source_perspectives": [],
 "regional_impacts": [],
 "regional_categories": [],
 "verified_category": "",
 "key_takeaways": "",
 "core_drivers": []
}}"""
        return safe_encode(prompt)

    def _build_stage2_prompt(
        self,
        topic_title: str,
        category: str,
        topic_summary: str,
        stage1_output: str
    ) -> str:
        """Build Stage 2: Engagement Elements prompt."""
        
        prompt = f"""You are generating user-facing engagement elements for a news intelligence platform.

Use the analysis provided to create concise presentation elements.

════════════════════════
TOPIC INFORMATION
════════════════════════

title: "{topic_title}"
category: "{category}"
summary:
{topic_summary[:1000]}

analysis:
{stage1_output}

════════════════════════
TASKS
════════════════════════

1. INTELLIGENCE CARD
Create a homepage intelligence card.
Provide:
- category
- icon (emoji)
- title (3–6 words)
- description (one sentence, max 15 words)
- trend_percentage (estimate like "+12%" or "-8%")
- is_positive (true or false)

2. CONTEXTUAL POLL
Create an engaging poll question related to the topic context.
Provide:
- question
- options (exactly 4 distinct choices)

════════════════════════
OUTPUT RULES
════════════════════════
Return STRICT valid JSON only.
Do not include explanations, markdown, or comments.

════════════════════════
OUTPUT FORMAT
════════════════════════
{{
 "intelligence_card": {{}},
 "poll": {{
   "question": "",
   "options": ["", "", "", ""]
 }}
}}"""
        return safe_encode(prompt)
