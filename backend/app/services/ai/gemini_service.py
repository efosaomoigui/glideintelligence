import logging
import os
import json
from typing import Dict, Any, Optional
# New library import - will be handled lazily to prevent module-level import errors
# from google import genai
# from google.genai import types

logger = logging.getLogger(__name__)

class GeminiService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        from app.config import settings
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")
            
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in settings or environment.")
            return

        try:
            from google import genai
            # Initialize the new client
            self.client = genai.Client(api_key=self.api_key)
            # Set default model
            self.model_name = "gemini-2.0-flash" 
        except ImportError:
            logger.error("❌ google-genai SDK not found. Please install with: pip install google-genai")
            self.client = None

    def analyze_article(self, text: str) -> Dict[str, Any]:
        """
        Analyze article text to extract Summary, Sentiment, and Regional Framing.
        Returns a structured JSON object.
        """
        if not self.client:
            raise ImportError("Gemini client not initialized (google-genai missing).")

        from google.genai import types

        # Truncate text to stay safe within token limits
        text = text[:30000] 

        prompt = f"""
You are a senior news analyst for an African business intelligence platform.
Analyze the following news text and return a strictly valid JSON object.

Your response MUST follow this schema exactly:
{{
  "summary": "Full summary here (4-6 complete sentences)",
  "facts": ["Fact 1", "Fact 2", "Fact 3"],
  "sentiment": {{
    "positive": 0.0,
    "neutral": 0.0,
    "negative": 0.0
  }},
  "regional_framing": {{
    "impact_score": 7,
    "economic_impact": "String here",
    "political_impact": "String here",
    "social_impact": "String here"
  }}
}}

CRITICAL: 
1. The "summary" must contain 4 to 6 COMPLETE sentences with specific stakeholders and figures.
2. Every string value MUST be enclosed in double quotes. 
3. DO NOT return any text other than the JSON object.

News Text:
{text[:12000]}
"""

        try:
            print(f"DEBUG: Calling Gemini {self.model_name} for analysis (JSON Mode)...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1500,
                    temperature=0.4,
                    response_mime_type='application/json'
                )
            )
            print(f"DEBUG: Gemini response received. Length: {len(response.text)}")
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(clean_text)
            except json.JSONDecodeError as je:
                print(f"ERROR: Gemini returned invalid JSON. Raw response follows:")
                print("="*50)
                print(response.text)
                print("="*50)
                raise je
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}", exc_info=True)
            print(f"Gemini analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Gemini API (google-genai).
        """
        if not self.api_key:
            raise ValueError("Gemini API Key is missing.")
            
        if not self.client:
            raise ImportError("Gemini client not initialized (google-genai missing).")

        from google.genai import types

        # Safety truncation
        prompt = prompt[:40000]

        try:
            target_model = model if model else self.model_name
            # Fallback to 1.5-flash or 2.0-flash as 'gemini-pro' might be gone or v1beta only
            if target_model == "gemini-pro": 
                 target_model = "gemini-2.0-flash"

            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"❌ Gemini generation failed (Model: {target_model}): {e}", exc_info=True)
            raise e
