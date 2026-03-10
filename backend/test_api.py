import urllib.request
import traceback

try:
    with urllib.request.urlopen("http://localhost:8000/api/home", timeout=5) as response:
        data = response.read().decode("utf-8")
        print("Raw Response Length:", len(data))
        import json
        try:
            parsed = json.loads(data)
            print("Successfully parsed JSON.")
        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            print("Prefix:", data[:500])
except Exception as e:
    traceback.print_exc()
