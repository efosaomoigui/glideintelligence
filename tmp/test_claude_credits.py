import os
import sys
from dotenv import load_dotenv
import anthropic

# Load .env
load_dotenv('backend/.env')

api_key = os.getenv("ANTHROPIC_API_KEY")
model = "claude-opus-4-6" # Using the name user provided

print(f"Testing Claude API with key: {api_key[:10]}...")

try:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=10,
        messages=[{"role": "user", "content": "Hello, are you working?"}]
    )
    print("Claude API is working!")
    print(f"Response: {response.content[0].text}")
except Exception as e:
    print(f"Claude API failed: {e}")
