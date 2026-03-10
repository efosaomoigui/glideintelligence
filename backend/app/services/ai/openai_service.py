import logging
import os
from typing import Optional
import openai

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self, api_key: str = None):
        if not api_key:
            from app.config import settings
            api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in settings or environment.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    def generate_content(
        self,
        prompt: str,
        model: str = "gpt-4-turbo",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using OpenAI API.
        """
        if not self.is_available():
            raise ValueError("OpenAI API client is not initialized. Check API Key.")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise e
