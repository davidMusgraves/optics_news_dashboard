import schedule
import time
from digester.rss_fetcher import fetch_articles
from digester.categorizer import categorize_article


def job():
    print("[Digester] Running fetch + categorize job")
    articles = fetch_articles()
    for a in articles:
        tags = categorize_article(a)
        print(f"- {a['title'][:60]}... → Tags: {tags}")


def run_scheduled_tasks():
    schedule.every().day.at("08:00").do(job)
    schedule.every().day.at("20:00").do(job)

    print("[Digester] Scheduler started. Waiting for jobs...")
    while True:
        schedule.run_pending()
        time.sleep(30)
