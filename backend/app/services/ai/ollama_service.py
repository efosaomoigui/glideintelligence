"""
Ollama Service - Local AI Provider Integration
"""
import logging
import requests
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama local AI models."""
    
    def __init__(self, base_url: str = None):
        if base_url:
            self.base_url = base_url
        else:
             import os
             self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self.api_url = f"{self.base_url}/api"
    
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            return False
    
    def list_models(self) -> list:
        """List available models in Ollama."""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                return response.json().get("models", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate text using Ollama model.
        
        Args:
            model: Model name (e.g., "llama3.2:3b-instruct")
            prompt: Input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.info(f"Calling Ollama with model: {model}")
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=300  # Increased timeout for CPU-based inference
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise Exception(f"Ollama API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise Exception("Ollama request timed out after 300 seconds")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def chat(
        self,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Chat-style interaction with Ollama model.
        
        Args:
            model: Model name
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            logger.info(f"Ollama chat with model: {model}")
            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                logger.error(f"Ollama chat error: {response.status_code}")
                raise Exception(f"Ollama chat failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise
    
    def analyze_article(self, article_text: str, model: str = "llama3.2:latest") -> Dict:
        """
        Analyze article content and return structured intelligence data.
        
        Args:
            article_text: The article content to analyze
            model: Ollama model to use (default: llama3:latest)
            
        Returns:
            Dict with summary, facts, regional_framing, and sentiment
        """
        try:
            prompt = f"""Analyze the following news article and provide a structured analysis.

Article:
{article_text[:3000]}  # Limit to avoid token limits

Please provide:
1. A concise 60-second summary (2-3 sentences)
2. 3-5 key facts as bullet points
3. Regional framing analysis (how different regions might view this)
4. Overall sentiment (positive, negative, or neutral)

Format your response as JSON with keys: summary, facts (array), regional_framing (object), sentiment"""

            response_text = self.generate(model, prompt, temperature=0.3, max_tokens=1500)
            
            # Try to parse JSON from response
            try:
                # Extract JSON if wrapped in markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                result = json.loads(response_text)
                
                # Ensure required fields exist
                if "summary" not in result:
                    result["summary"] = "Analysis completed via Ollama"
                if "facts" not in result:
                    result["facts"] = ["Analyzed using local Llama3 model"]
                if "regional_framing" not in result:
                    result["regional_framing"] = {}
                if "sentiment" not in result:
                    result["sentiment"] = "neutral"
                
                return result
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON from Ollama response, using fallback")
                return {
                    "summary": response_text[:500] if response_text else "Analysis completed",
                    "facts": ["Analyzed using local Llama3 model"],
                    "regional_framing": {},
                    "sentiment": "neutral"
                }
                
        except Exception as e:
            logger.error(f"Ollama article analysis failed: {e}")
            raise

# Global instance
ollama_service = OllamaService()
