import requests
import json

def verify_ollama():
    # List models first
    print("Listing models via API...")
    try:
        list_response = requests.get("http://localhost:11434/api/tags")
        print(f"List response: {list_response.status_code}")
        print(f"Models: {list_response.text}")
    except Exception as e:
        print(f"List failed: {e}")

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "tinyllama:latest",
        "prompt": "Hello",
        "stream": False
    }
    try:
        print(f"Testing model: {payload['model']}")
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 404:
            print("Trying without tag...")
            payload["model"] = "llama3"
            response = requests.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_ollama()
