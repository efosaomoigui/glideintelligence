import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.source import Source, SourceType, SourceHealth
from app.models.article import RawArticle

logger = logging.getLogger(__name__)

import feedparser
import time

class CrawlerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_articles(self, source: Source) -> int:
        """
        Fetch articles from a given source based on its type.
        Returns the number of articles fetched (simulated or real).
        """
        if source.type == SourceType.RSS:
            count = await self._fetch_rss(source)
        elif source.type == SourceType.API:
            count = await self._fetch_api(source)
        elif source.type == SourceType.WEBSITE:
            count = await self._fetch_website(source)
        else:
            logger.warning(f"Unknown source type {source.type} for source {source.name}")
            count = 0
        
        return count

    async def validate_source(self, source_type: str, url: str) -> bool:
        """Validate if the source URL is reachable and matches the type."""
        # TODO: Implement actual network check
        if source_type == SourceType.RSS:
            # Simple check for now
            return True
        return True

    async def _fetch_rss(self, source: Source) -> int:
        from app.models.article import RawArticle
        
        logger.info(f"Fetching RSS feed from {source.url}")
        
        def parse_feed_sync(url):
             return feedparser.parse(url)
             
        loop = asyncio.get_event_loop()
        logger.info(f"Parsing feed: {source.url}")
        feed = await loop.run_in_executor(None, parse_feed_sync, source.url)
        
        logger.info(f"Feed keys: {feed.keys()}")
        logger.info(f"Entries count: {len(feed.entries)}")
        if hasattr(feed, 'bozo') and feed.bozo:
             logger.warning(f"Feed Bozo: {feed.bozo}, Exception: {feed.get('bozo_exception')}")
        
        if not feed.entries and "/feed" not in source.url and "rss" not in source.url:
             # Try common feed paths if direct URL fails
             for suffix in ["/feed", "/rss", "/rss.xml", "/feed.xml"]:
                 feed = await loop.run_in_executor(None, parse_feed_sync, source.url.rstrip('/') + suffix)
                 if feed.entries:
                     break
        
        if not feed.entries:
            logger.warning(f"No entries found for {source.url}")
            return 0
            
        import hashlib
        
        new_count = 0
        seen_urls = set()
        for entry in feed.entries:
            if entry.link in seen_urls:
                continue
            seen_urls.add(entry.link)
            
            # Content cleaning
            content = entry.get("summary", "") or entry.get("description", "") or ""
            title = entry.title or ""
            
            # Create content hash (Title + Link) to detect duplicates more robustly
            hash_input = f"{title}{entry.link}".encode('utf-8')
            content_hash = hashlib.sha256(hash_input).hexdigest()

            # Check for duplicates using URL or Content Hash
            exists_query = select(RawArticle).where(
                or_(RawArticle.url == entry.link, RawArticle.content_hash == content_hash)
            )
            exists = await self.db.execute(exists_query)
            if exists.scalar_one_or_none():
                continue
                
            # Create Raw Article
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                 published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            else:
                 published = datetime.now()

            # Word count approximation
            word_count = len(content.split())
            
            # Snippet (first 200 chars)
            snippet = content[:200] + "..." if len(content) > 200 else content

            article = RawArticle(
                source_id=source.id,
                external_id=entry.get("id", entry.link),
                title=title,
                url=entry.link,
                content=content,
                published_at=published,
                author=entry.get("author", "Unknown"),
                image_url=None, 
                language="en", # Defaulting to en for now
                word_count=word_count,
                snippet=snippet,
                content_hash=content_hash,
                is_duplicate=False
            )
            self.db.add(article)
            new_count += 1
            
        await self.db.commit()
        return new_count

    async def _fetch_api(self, source: Source) -> int:
        # Placeholder for API fetching logic (e.g., using httpx)
        logger.info(f"Fetching via API from {source.url}")
        await asyncio.sleep(1)
        return 10 # Mock count

    async def _fetch_website(self, source: Source) -> int:
        # Placeholder for Website scraping logic (e.g., using playright or beautifulsoup)
        logger.info(f"Scraping website {source.url}")
        await asyncio.sleep(2)
        return 3 # Mock count

