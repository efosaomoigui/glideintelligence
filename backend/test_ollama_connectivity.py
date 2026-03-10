"""Test Ollama API connectivity"""
import requests
import json

# Test 1: Check if Ollama is running
print("Test 1: Checking Ollama service...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Models: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"  Error: {e}")

# Test 2: Try to generate with llama3:latest
print("\nTest 2: Testing generation with llama3:latest...")
try:
    payload = {
        "model": "llama3:latest",
        "prompt": "Say hello in one sentence.",
        "stream": False
    }
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=30
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")
