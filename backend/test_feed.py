import feedparser
import sys

url = "http://feeds.bbci.co.uk/news/business/rss.xml"
print(f"Testing feedparser with URL: {url}")

try:
    feed = feedparser.parse(url)
    print(f"Bozo: {feed.get('bozo')}")
    print(f"Bozo Exception: {feed.get('bozo_exception')}")
    print(f"Entries found: {len(feed.entries)}")
    if len(feed.entries) > 0:
        print(f"First entry title: {feed.entries[0].title}")
    else:
        print("No entries found.")
        print(f"Feed details: {feed}")
except Exception as e:
    print(f"Exception Message: {e}")
