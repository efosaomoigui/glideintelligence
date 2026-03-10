#!/bin/bash
# Pull LLaMA 3.2 3B Instruct model into Ollama

echo "=================================================="
echo "Pulling LLaMA 3.2 3B Instruct Model"
echo "=================================================="
echo ""
echo "This will download ~2GB of data."
echo "Please wait, this may take 5-10 minutes..."
echo ""

# Pull the model
docker exec -it ollama ollama pull llama3.2:3b-instruct

echo ""
echo "=================================================="
echo "Model Pull Complete!"
echo "=================================================="
echo ""
echo "Verifying model..."
docker exec -it ollama ollama list

echo ""
echo "Testing model..."
docker exec -it ollama ollama run llama3.2:3b-instruct "Say hello in one sentence"

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run: python seed_ollama_provider.py"
echo "2. Run: python test_ollama_provider.py"
echo "3. Test AI analysis with Ollama as fallback"
