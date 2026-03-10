"""Test login endpoint directly"""
import requests

print("Testing login endpoint...")
print("="*70)

# Test 1: Check if backend is running
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"[OK] Backend is running - Health check: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Backend not accessible: {e}")
    print("\nPlease start the backend with:")
    print("  uvicorn app.main:app --reload")
    exit(1)

# Test 2: Try login
print("\nTesting login with admin@example.com / admin123...")
try:
    response = requests.post(
        "http://localhost:8000/api/auth/token",
        data={
            "username": "admin@example.com",
            "password": "admin123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n[OK] Login successful!")
        data = response.json()
        print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
        
        # Check if cookie was set
        if 'access_token' in response.cookies:
            print("[OK] Cookie was set")
        else:
            print("[WARN] Cookie was not set (may be expected)")
    else:
        print(f"\n[FAIL] Login failed with status {response.status_code}")
        
except Exception as e:
    print(f"[FAIL] Error during login: {e}")

print("="*70)
