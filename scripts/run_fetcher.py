# scripts/run_fetcher.py
import argparse
import os
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from newspaper import Article as NPArticle
from readability import Document

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from data.db.article_model import get_session, Article

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OpticsNewsDigester/1.0; +https://example.com/bot)"
}

def load_sources(yaml_path="config/sources.yaml"):
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("rss_feeds", [])

def fetch_full_text(url, timeout=15):
    """
    Try newspaper3k first; if that fails, fallback to readability.
    Return plain text; raise on hard failures.
    """
    # Try newspaper3k
    try:
        art = NPArticle(url)
        art.download()
        art.parse()
        text = (art.text or "").strip()
        if text:
            return text
    except Exception:
        pass

    # Fallback: requests + readability
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    doc = Document(resp.text)
    html = doc.summary(html_partial=True)
    # Strip to text
    soup = BeautifulSoup(html, "html5lib")
    text = soup.get_text(separator="\n").strip()
    return text

def fetch_feed(feed):
    name = feed.get("name", "Unnamed")
    url = feed["url"]
    print(f"[RSS] Fetching from: {name} → {url}")
    parsed = feedparser.parse(url)
    entries = parsed.entries or []
    print(f"[RSS] Found {len(entries)} entries.")
    return entries

def safe_get(obj, *keys, default=""):
    for k in keys:
        v = getattr(obj, k, None)
        if v:
            return v
    return default

def run_fetch(sources, limit=None, delay=1.0, fulltext=True):
    session = get_session()
    total_new = 0
    for feed in sources:
        entries = fetch_feed(feed)
        if limit:
            entries = entries[:limit]
        for e in entries:
            link = safe_get(e, "link")
            if not link:
                continue
            # dedupe on link
            if session.query(Article).filter_by(link=link).first():
                continue

            title = safe_get(e, "title")
            summary = safe_get(e, "summary", "description")
            published = safe_get(e, "published", "updated", "pubDate")
            source = feed.get("name", urlparse(link).netloc)

            content = None
            if fulltext and link.startswith("http"):
                try:
                    content = fetch_full_text(link)
                except Exception as ex:
                    print(f"[Warn] Full-text failed for {link}: {ex}")
                    content = None

            art = Article(
                title=title,
                link=link,
                summary=summary,
                content=content or summary,  # fallback to summary
                published=published,
                source=source,
                tags="",  # will be filled by processing step
                fetched_at=datetime.utcnow(),
            )
            session.add(art)
            session.commit()
            total_new += 1

            time.sleep(delay)  # be polite to sites
    print(f"[Fetch] Inserted {total_new} new articles.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch RSS and (optionally) full text.")
    parser.add_argument("--sources", default="config/sources.yaml", help="Path to YAML sources")
    parser.add_argument("--limit", type=int, default=None, help="Limit entries per feed")
    parser.add_argument("--no-fulltext", action="store_true", help="Disable full-text scraping")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between article fetches (sec)")
    args = parser.parse_args()

    sources = load_sources(args.sources)
    run_fetch(sources, limit=args.limit, delay=args.delay, fulltext=(not args.no_fulltext))
