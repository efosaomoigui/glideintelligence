import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer  # lazy import
            self.model = SentenceTransformer(model_name)
        except ModuleNotFoundError:
            logger.warning("sentence_transformers not installed — embeddings disabled. Clustering will use title hashing fallback.")
        except Exception as e:
            logger.error(f"Failed to load embedding model {model_name}: {e}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a vector embedding for the given text."""
        if not self.model:
            logger.warning("Embedding model not loaded, returning zero vector.")
            return [0.0] * 384
        
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * 384

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if not self.model:
            logger.warning("Embedding model not loaded, returning zero vectors for batch.")
            return [[0.0] * 384 for _ in texts]
        
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [[0.0] * 384 for _ in texts]
