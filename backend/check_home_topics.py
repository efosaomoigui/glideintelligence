import urllib.request
import json

try:
    r = urllib.request.urlopen("http://localhost:8000/api/home")
    d = json.loads(r.read())
    trending = d.get("trending_topics", [])
    print(f"Trending Topics Count: {len(trending)}")
    for t in trending:
        print(f"- {t.get('title')}")
except Exception as e:
    print(f"Error: {e}")
