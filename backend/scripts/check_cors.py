import requests
import sys

def check_cors():
    url = "http://localhost:8000/api/home"
    origin = "http://localhost:3000"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET"
    }
    
    print(f"Checking CORS for {url} with Origin {origin}...")
    try:
        response = requests.options(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            print(f"{k}: {v}")
            
        if "access-control-allow-origin" in response.headers:
            print("\nSUCCESS: CORS headers present.")
            if response.headers["access-control-allow-origin"] == origin:
                print("Origin matched correctly.")
            else:
                print(f"Origin mismatch: {response.headers['access-control-allow-origin']}")
        else:
            print("\nFAILURE: No Access-Control-Allow-Origin header found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cors()
