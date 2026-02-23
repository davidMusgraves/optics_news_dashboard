import yaml
import feedparser
import requests


def load_sources(config_path="config/sources.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)["rss_feeds"]


def fetch_articles():
    sources = load_sources()
    articles = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSSDigester/1.0; +https://yourdomain.com/bot)"
    }

    for source in sources:
        print(f"[RSS] Fetching from: {source['name']} → {source['url']}")
        try:
            response = requests.get(source["url"], headers=headers, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as e:
            print(f"[ERROR] Failed to fetch {source['name']}: {e}")
            continue

        print(f"[RSS] Found {len(feed.entries)} entries.")
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            published = entry.get("published", entry.get("pubDate", "")).strip()

            if title and link:
                articles.append({
                    "source": source["name"],
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published,
                })
            else:
                print("[RSS] Skipping entry with missing title or link.")

    print(f"[RSS] Total parsed articles: {len(articles)}")
    return articles
