import requests
import sys

def verify_trending():
    url = "http://localhost:8000/api/topics/trending?limit=10&filter=today"
    try:
        print(f"Fetching {url}...")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Endpoint returned 200 OK")
            data = response.json()
            print(f"Items: {len(data.get('items', []))}")
        else:
            print(f"FAILURE: Endpoint returned {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_trending()
