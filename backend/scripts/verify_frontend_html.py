import requests
from bs4 import BeautifulSoup
import sys

BASE_URL = "http://localhost:3000"

def check_url(url, element_checks):
    print(f"Checking {url}...")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to fetch {url}: Status {response.status_code}")
            return False
        
        soup = BeautifulSoup(response.content, 'html.parser')
        all_passed = True
        
        for check_name, check_fn in element_checks.items():
            if check_fn(soup):
                print(f"✅ {check_name} passed")
            else:
                print(f"❌ {check_name} failed")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return False

def verify_homepage(soup):
    # Check for Hero section
    hero = soup.find('section', class_=lambda c: c and 'hero' in c.lower() or 'featured' in c.lower())
    # Or just check for specific text or links we expect
    read_full = soup.find('a', string=lambda s: s and "Read Full Intelligence" in s)
    return read_full is not None

def verify_latest_news(soup):
    # Check for article list
    articles = soup.find_all('article')
    return len(articles) > 0

def check_homepage():
    return check_url(BASE_URL, {
        "Hero 'Read Full Intelligence' Link": verify_homepage,
        "Latest News Articles": verify_latest_news
    })

if __name__ == "__main__":
    print("Starting Frontend HTML Verification...")
    homepage_ok = check_homepage()
    
    if homepage_ok:
        print("\n🎉 Homepage HTML verification passed!")
        sys.exit(0)
    else:
        print("\n⚠️ Homepage HTML verification failed.")
        sys.exit(1)
