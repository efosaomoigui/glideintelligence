import logging
import os
from typing import Optional, Dict, Any
import anthropic

logger = logging.getLogger(__name__)

class ClaudeService:
    """Service for interacting with Anthropic's Claude API."""
    
    def __init__(self, api_key: str = None):
        if not api_key:
            from app.config import settings
            api_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
            
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found in settings or environment.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    def generate_content(
        self,
        prompt: str,
        model: str = "claude-3-sonnet-20240229",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Claude API.
        """
        if not self.is_available():
            raise ValueError("Claude API client is not initialized. Check API Key.")

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            raise e
