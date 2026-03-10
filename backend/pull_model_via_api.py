import requests
import json

def pull_model():
    url = "http://localhost:11434/api/pull"
    payload = {
        "name": "tinyllama:latest",
        "stream": False 
    }
    print(f"Requesting pull for {payload['name']}...")
    try:
        response = requests.post(url, json=payload, stream=True)
        print(f"Response Status: {response.status_code}")
        
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pull_model()
