import logging
from typing import List, Dict, Optional
import torch
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

logger = logging.getLogger(__name__)

class LocalInferenceService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalInferenceService, cls).__new__(cls)
            cls._instance._initialize_pipelines()
        return cls._instance

    def _initialize_pipelines(self):
        """
        Initialize Hugging Face pipelines/models.
        Loads models into memory (RAM usage warning).
        """
        logger.info("Initializing Local AI Models...")
        device = "cpu" # Force CPU for compatibility
        if torch.cuda.is_available():
            device = "cuda"

        try:
            # 1. Summarization (BART) - Loaded directly
            logger.info("Loading Summarization Model (facebook/bart-large-cnn)...")
            self.summ_model_name = "facebook/bart-large-cnn"
            self.summ_tokenizer = AutoTokenizer.from_pretrained(self.summ_model_name)
            self.summ_model = AutoModelForSeq2SeqLM.from_pretrained(self.summ_model_name)
            if device == "cuda":
                self.summ_model = self.summ_model.to(device)
            
            # 2. Sentiment (DistilBERT)
            logger.info("Loading Sentiment Model (distilbert-base-uncased-finetuned-sst-2-english)...")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis", 
                model="distilbert-base-uncased-finetuned-sst-2-english", 
                device=-1 if device == "cpu" else 0
            )
            
            # 3. Zero-Shot Classification (BART-MNLI) - For Categorization/Framing
            logger.info("Loading Zero-Shot Model (facebook/bart-large-mnli)...")
            self.classifier = pipeline(
                "zero-shot-classification", 
                model="facebook/bart-large-mnli", 
                device=-1 if device == "cpu" else 0
            )
            
            logger.info("All Local AI Models Loaded Successfully.")
            
        except Exception as e:
            logger.error(f"Error loading AI models: {e}")
            raise e

    def generate_summary(self, text: str, max_length: int = 150, min_length: int = 50) -> str:
        """
        Generate a summary using BART (Direct Generation).
        """
        # BART max token limit is 1024.
        truncated_text = text[:3000] 
        
        try:
            inputs = self.summ_tokenizer([truncated_text], max_length=1024, return_tensors="pt", truncation=True)
            
            # Move inputs to device if needed
            if hasattr(self.summ_model, "device") and self.summ_model.device.type == "cuda":
                inputs = {k: v.to(self.summ_model.device) for k, v in inputs.items()}

            summary_ids = self.summ_model.generate(
                inputs["input_ids"], 
                num_beams=4, 
                max_length=max_length, 
                min_length=min_length, 
                early_stopping=True
            )
            
            summary = self.summ_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "Summary generation failed."

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using DistilBERT.
        Returns normalized scores (approx).
        """
        truncated_text = text[:512]
        try:
            result = self.sentiment_analyzer(truncated_text)[0]
            # Result format: {'label': 'POSITIVE', 'score': 0.99}
            
            label = result['label']
            score = result['score']
            
            # Map to our schema
            sentiment = {
                "positive": 0.0,
                "neutral": 0.0, 
                "negative": 0.0
            }
            
            if label == "POSITIVE":
                sentiment["positive"] = score
                sentiment["negative"] = 1.0 - score
            else:
                sentiment["negative"] = score
                sentiment["positive"] = 1.0 - score
                
            # DistilBERT is binary. We can infer neutral if scores are balanced or use a different model.
            # For now, simplistic mapping.
            return sentiment
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"positive": 0.0, "neutral": 1.0, "negative": 0.0}

    def analyze_framing(self, text: str) -> Dict[str, str]:
        """
        Use Zero-Shot classification to determine the 'frame' or impact area.
        """
        candidate_labels = ["Economic Impact", "Political Stability", "Social/Cultural", "Security", "Technology/Innovation", "International Relations"]
        truncated_text = text[:1024]
        
        try:
            result = self.classifier(truncated_text, candidate_labels)
            
            # Return top 2 frames
            scores = result['scores']
            labels = result['labels']
            
            framing = {}
            # Top 1
            framing["Primary Frame"] = f"{labels[0]} ({scores[0]:.2f})"
            # Top 2
            framing["Secondary Frame"] = f"{labels[1]} ({scores[1]:.2f})"
            
            return framing
        except Exception as e:
            logger.error(f"Framing analysis failed: {e}")
            return {"Error": "Could not analyze framing"}

# Global instance for easy import
# Note: In a multiprocess environment (Celery workers), this will be instantiated once per worker process.
local_inference = LocalInferenceService()
