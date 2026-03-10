
import sys
import os
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add parent dir to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.ai.ollama_service import OllamaService

def main():
    print("Testing OllamaService...")
    service = OllamaService()
    
    print("Checking availability...")
    if not service.is_available():
        print("FAIL: Ollama not available")
        return

    print("OK: Ollama available")
    
    print("Listing models...")
    models = service.list_models()
    print(f"Models: {models}")
    
    # Test generation
    model = "tinyllama:latest"
    print(f"Testing generation with model: {model}")
    try:
        response = service.generate(model, "Say hello!", max_tokens=20)
        print(f"Response: {response}")
    except Exception as e:
        print(f"FAIL: Generation failed: {e}")

    # Test analyze_article
    print("Testing analyze_article...")
    try:
        # Create a mock article text
        article_text = "This is a test article about artificial intelligence. AI is transforming industries."
        result = service.analyze_article(article_text, model=model)
        print(f"Analysis result keys: {result.keys()}")
        print(f"Summary: {result.get('summary')}")
    except Exception as e:
        print(f"FAIL: Analysis failed: {e}")

if __name__ == "__main__":
    main()
