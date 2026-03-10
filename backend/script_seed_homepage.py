import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.database import AsyncSessionLocal
from app.models import Source, RawArticle, Topic
from sqlalchemy import select

# Mock Data matching the design
ARTICLES = [
    {
        "title": "Senate Passes Landmark Electoral Reform Bill Ahead of 2027 Cycle",
        "description": "The Nigerian Senate has approved sweeping amendments to the Electoral Act in a 79\u201332 vote, introducing electronic transmission of results as mandatory.",
        "content": "Full content here...",
        "category": "Politics",
        "source": "Channels TV",
        "url": "https://channelstv.com/reform-bill-2027",
        "published_minutes_ago": 30
    },
    {
        "title": "Dangote Refinery Achieves Full Capacity, Begins Export to 4 African Nations",
        "description": "The refinery creates a new export corridor for Nigeria.",
        "content": "Content...",
        "category": "Business",
        "source": "BusinessDay",
        "url": "https://businessday.ng/dangote-export",
        "published_minutes_ago": 180
    },
    {
        "title": "Inflation Eases to 27.2% as Food Prices Stabilise in January",
        "description": "NBS data shows a slight reprieve in consumer price index.",
        "content": "Content...",
        "category": "Economy",
        "source": "The Punch",
        "url": "https://punchng.com/inflation-eases",
        "published_minutes_ago": 300
    },
    {
        "title": "Operation Hadin Kai Claims Elimination of 87 Insurgents in Borno Offensive",
        "description": "Military spokesman confirms successful air raids.",
        "content": "Content...",
        "category": "Security",
        "source": "Channels TV",
        "url": "https://channelstv.com/borno-offensive",
        "published_minutes_ago": 420
    },
    {
        "title": "Nigerian Fintech Moniepoint Reaches $1B Valuation After Series D Round",
        "description": "The unicorn status was confirmed after the latest funding round led by Google Ventures.",
        "content": "Content...",
        "category": "Tech",
        "source": "TechCabal",
        "url": "https://techcabal.com/moniepoint-unicorn",
        "published_minutes_ago": 540
    },
    {
        "title": "Super Eagles Draw Morocco in AFCON 2027 Qualifying Group Stage",
        "description": "Tough road ahead for the national team.",
        "content": "Content...",
        "category": "Sports",
        "source": "Vanguard",
        "url": "https://vanguardngr.com/super-eagles-afcon",
        "published_minutes_ago": 720
    }
]

async def seed_homepage():
    print("Seeding homepage articles...")
    async with AsyncSessionLocal() as db:
        for item in ARTICLES:
            # 1. Get or Create Source
            stmt = select(Source).where(Source.name == item["source"])
            source = (await db.execute(stmt)).scalar_one_or_none()
            if not source:
                domain = f"{item['source'].lower().replace(' ', '')}.com"
                url = f"https://{domain}"
                source = Source(
                    name=item["source"], 
                    url=url, 
                    domain=domain,
                    is_active=True
                )
                db.add(source)
                await db.flush()
                print(f"Created Source: {source.name}")

            # 2. Check if article exists
            stmt = select(RawArticle).where(RawArticle.url == item["url"])
            existing = (await db.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                article = RawArticle(
                    source_id=source.id,
                    title=item["title"],
                    description=item["description"],
                    content=item["content"],
                    url=item["url"],
                    external_id=item["url"], # simple mock
                    category=item["category"],
                    published_at=(datetime.utcnow() - timedelta(minutes=item["published_minutes_ago"])).isoformat()
                )
                db.add(article)
                print(f"Added Article: {item['title']}")
            else:
                print(f"Skipped (Exists): {item['title']}")
        
        await db.commit()
        print("Homepage seeding complete.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_homepage())
