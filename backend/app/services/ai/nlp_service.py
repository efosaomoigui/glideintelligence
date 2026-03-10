from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self, model_name: str = "en_core_web_sm"):
        self.nlp = None
        try:
            import spacy  # lazy import — spacy may not be installed
            self.nlp = spacy.load(model_name)
        except ModuleNotFoundError:
            logger.warning("spaCy not installed — entity extraction disabled. Returning empty entities.")
        except Exception as e:
            logger.error(f"Failed to load spaCy model {model_name}: {e}")

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities (Person, Org, GPE) from text."""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_
                })
        
        # Deduplicate and count
        seen = {}
        for ent in entities:
            key = (ent["text"], ent["label"])
            seen[key] = seen.get(key, 0) + 1
            
        return [{"text": k[0], "label": k[1], "count": v} for k, v in seen.items()]
