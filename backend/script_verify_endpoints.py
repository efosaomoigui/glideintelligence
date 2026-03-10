import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000/api"

async def test_topic_slug():
    slug = "fuel-subsidy-removal" # Default test slug
    print(f"Testing Topic Slug endpoint...")
    async with httpx.AsyncClient() as client:
        # Get home to find a trending topic
        try:
            resp = await client.get(f"{BASE_URL}/home")
            if resp.status_code == 200:
                data = resp.json()
                trending = data.get("trending_topics", [])
                if trending:
                    topic = trending[0]
                    title = topic['title']
                    slug = title.strip().replace(" ", "-").lower()
                    print(f"Found trending topic: {title} -> slug: {slug}")
                else:
                    print("No trending topics found on home. Using default slug: fuel-subsidy-removal")
            else:
                print(f"Failed to fetch home data: {resp.status_code}. Using default slug.")
        except httpx.RequestError as e:
             print(f"Connection error to {BASE_URL}: {e}")
             return

        print(f"Testing slug: {slug}")

        try:
            resp = await client.get(f"{BASE_URL}/topic/slug/{slug}")
            if resp.status_code == 200:
                t_data = resp.json()
                print(f"[SUCCESS] Topic by slug found: {t_data.get('title')}")
                if 'analysis' in t_data:
                    summary = t_data['analysis'].get('summary', '')[:50]
                    print(f"   - Analysis Summary: {summary}...")
                else:
                    print(f"   - [WARN] No analysis found.")
            else:
                print(f"[FAIL] Failed to fetch topic by slug: {resp.status_code} {resp.text}")
        except httpx.RequestError as e:
            print(f"Connection error: {e}")

async def test_vertical():
    category = "Business" # Assumption
    print(f"\nTesting Vertical endpoint: {category}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/vertical/{category}")
            if resp.status_code == 200:
                 data = resp.json()
                 articles = data.get('featured_articles', [])
                 trending = data.get('trending_topics', [])
                 print(f"[SUCCESS] Vertical data received. Articles: {len(articles)}, Trending: {len(trending)}")
            else:
                print(f"[FAIL] Failed to fetch vertical: {resp.status_code} {resp.text}")
        except httpx.RequestError as e:
            print(f"Connection error: {e}")

async def test_home():
    print(f"\nTesting Home endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/home")
            if resp.status_code == 200:
                data = resp.json()
                hero = data.get('hero_article')
                trending = data.get('trending_topics', [])
                latest = data.get('latest_articles', [])
                print(f"[SUCCESS] Home data received.")
                print(f"   - Hero: {hero.get('title') if hero else 'None'}")
                print(f"   - Trending: {len(trending)}")
                print(f"   - Latest: {len(latest)}")
            else:
                print(f"[FAIL] Failed to fetch home: {resp.status_code} {resp.text}")
        except httpx.RequestError as e:
            print(f"Connection error: {e}")

async def main():
    await test_topic_slug()
    await test_vertical()
    await test_home()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
