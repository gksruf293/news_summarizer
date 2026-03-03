# src/pipeline.py

from src.fetch_news import fetch_top_headlines

def run_pipeline():
    print("Fetching news...")
    articles = fetch_top_headlines(country="us", page_size=20)
    print(f"Fetched {len(articles)} articles.")
