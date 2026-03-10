"""
Assign categories to existing topics based on their titles.
Uses canonical slugs from app/constants.py — single source of truth.
"""
import asyncio
import sys
import os

backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import AsyncSessionLocal
from app.models.topic import Topic
from app.constants import DEFAULT_CATEGORY
from sqlalchemy import select

KEYWORD_MAP = [
    ("politics",       ["senate", "president", "election", "law", "policy", "government", "minister", "tinubu", "governor", "apc", "pdp", "lp", "national assembly"]),
    ("economy",        ["naira", "inflation", "gdp", "cbn", "fiscal", "monetary", "currency", "forex", "interest rate", "budget", "debt"]),
    ("business",       ["market", "bank", "stock", "trade", "refinery", "dangote", "startup", "entrepreneur", "company", "merger", "acquisition", "investment", "profit", "revenue"]),
    ("sport",          ["football", "afcon", "match", "league", "sport", "super eagles", "npfl", "olympics", "fifa", "caf", "stadium", "athlete", "tournament"]),
    ("technology",     ["ai", "software", "digital", "cyber", "crypto", "tech", "fintech", "blockchain", "innovation", "semiconductor", "gadget", "smartphone"]),
    ("security",       ["police", "army", "attack", "kidnap", "bandit", "terror", "insurgent", "robbery", "piracy", "security", "military", "insecurity", "efcc"]),
    ("regional",       ["ecowas", "west africa", "cross-border", "bilateral", "diplomatic", "embassy", "foreign affairs"]),
    ("global-impact",  ["global impact", "international", "united nations", "un", "world bank", "imf", "treaty", "foreign aid"]),
    ("environment",    ["climate", "pollution", "deforestation", "niger delta", "oil spill", "conservation", "environment", "global warming", "carbon"]),
    ("social",         ["health", "education", "poverty", "community", "welfare", "gender", "youth", "women", "university", "hospital", "doctor"]),
]

async def assign_categories():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Topic))
        topics = result.scalars().all()
        
        print(f"Assigning categories to {len(topics)} topics...\n")
        
        for topic in topics:
            text = (topic.title + " " + (topic.description or "")).lower()
            assigned = DEFAULT_CATEGORY

            for category, keywords in KEYWORD_MAP:
                if any(kw in text for kw in keywords):
                    assigned = category
                    break

            topic.category = assigned
            print(f"  Topic {topic.id} [{assigned}] -> {topic.title[:60]}")
        
        await db.commit()
        print(f"\n✅ Categories assigned successfully!")

if __name__ == "__main__":
    asyncio.run(assign_categories())
