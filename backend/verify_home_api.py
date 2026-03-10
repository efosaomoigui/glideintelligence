import asyncio
import httpx
import json

async def verify_home_api():
    async with httpx.AsyncClient() as client:
        try:
            print("Fetching /api/home...")
            response = await client.get("http://localhost:8000/api/home")
            if response.status_code == 200:
                data = response.json()
                print("--- API Response ---")
                
                # Check Trending Topics
                topics = data.get("trending_topics", [])
                print(f"Trending Topics Count: {len(topics)}")
                if topics:
                    top_topic = topics[0]
                    print(f"Top Topic: {top_topic.get('title')}")
                    print(f"  Badge: {top_topic.get('badge')}")
                    print(f"  AI Brief: {top_topic.get('ai_brief')}")
                    print(f"  Updated At: {top_topic.get('updated_at_str')}")
                    print(f"  Perspectives Count: {len(top_topic.get('perspectives', []))}")
                    print(f"  Impact Count: {len(top_topic.get('impact', []))}")
                
                # Check Hero Article
                hero = data.get("hero_article")
                if hero:
                    print(f"\nHero Article: {hero.get('title')}")
                    print(f"  Category: {hero.get('category')}")
                    print(f"  Description: {hero.get('description')}")
                else:
                    print("\nHero Article: None")
                    
                # Check Latest Articles
                latest = data.get("featured_articles", [])
                print(f"\nLatest Articles Count: {len(latest)}")

            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_home_api())
