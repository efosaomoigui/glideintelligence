from typing import List, Dict, Optional
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import AIProvider, AIProviderType
from app.config import settings

# Import at top level to avoid async blocking issues with greenlet
from app.services.ai.gemini_service import GeminiService
from app.services.ai.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_active_providers(self) -> List[AIProvider]:
        """Fetch enabled AI providers ordered by priority."""
        query = select(AIProvider).where(AIProvider.enabled == True).order_by(AIProvider.priority.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def generate_summary_pipeline(self, articles_text: List[str]) -> Dict:
        """
        Run the multi-stage summarization pipeline using the highest priority enabled AI Provider.
        Dispatches to Gemini, OpenAI, or Local (BART) based on DB config.
        """
        active_providers = await self._get_active_providers()

        if not active_providers:
            # Fallback to Local if nothing configured, or raise error
            logger.warning("No AI providers enabled in DB. Attempting Local fallback.")
            # fallback logic or duplicate current local logic
            active_providers = [] 

        combined_text = "\n\n".join(articles_text[:5])
        
        last_error = None

        for provider in active_providers:
            try:
                logger.info(f"Attempting generation with provider: {provider.name} ({provider.model})")
                
                if provider.name.lower() in ["gemini", "google"]:
                    # Already imported at top level
                    gemini = GeminiService()
                    # GeminiService.analyze_article returns the full structured dict
                    result = gemini.analyze_article(combined_text)
                    result["provider"] = "Gemini (Cloud)"
                    result["confidence_score"] = 0.95
                    return result

                elif provider.name.lower() in ["ollama", "llama"]:
                    # Already imported at top level
                    ollama = OllamaService()
                    # OllamaService.analyze_article returns the full structured dict
                    result = ollama.analyze_article(combined_text, model=provider.model)
                    result["provider"] = f"Ollama ({provider.model})"
                    result["confidence_score"] = 0.90
                    return result
                
                elif provider.name.lower() in ["local", "huggingface"]:
                    from app.services.ai.local_inference import local_inference
                    # Stage 1: Summary
                    summary = local_inference.generate_summary(combined_text)
                    # Stage 2: Sentiment
                    sentiment = local_inference.analyze_sentiment(combined_text)
                    # Stage 3: Framing
                    regional_framing = local_inference.analyze_framing(combined_text)
                    
                    return {
                        "facts": ["Extracted via Local AI"], # Placeholder for now
                        "summary": summary,
                        "regional_framing": regional_framing,
                        "sentiment": sentiment,
                        "confidence_score": 0.85,
                        "provider": "Local (BART/BERT)"
                    }
                
                elif provider.name.lower() in ["claude", "anthropic"]:
                    from app.services.ai.claude_service import ClaudeService
                    claude = ClaudeService(api_key=provider.api_key)
                    
                    prompt = f"""Analyze the following news article(s) and return a structured intelligence brief.

ARTICLES:
{combined_text[:4000]}

Return a JSON object with exactly these fields:
{{
  "summary": "2-3 sentence executive summary of the key story",
  "facts": ["key fact 1", "key fact 2", "key fact 3"],
  "regional_framing": {{"west_africa": "how this affects the region", "global": "global context"}},
  "sentiment": "positive|negative|neutral",
  "confidence_score": 0.9
}}

Return ONLY the JSON object, no additional text."""

                    raw = claude.generate_content(prompt, model=provider.model, max_tokens=1000)
                    
                    # Parse JSON response
                    import json, re
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                    else:
                        data = {
                            "summary": raw[:500],
                            "facts": [],
                            "regional_framing": {},
                            "sentiment": "neutral",
                            "confidence_score": 0.8
                        }
                    
                    data["provider"] = f"Claude ({provider.model})"
                    data.setdefault("confidence_score", 0.9)
                    return data

                # Add OpenAI block here in future
            
            except Exception as e:
                logger.error(f"Provider {provider.name} failed: {e}")
                last_error = e
                continue  # Try next provider

        # If we get here, all providers failed
        if last_error:
            raise last_error
        else:
            raise Exception("No AI providers available or enabled.")
