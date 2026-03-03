# src/pipeline.py

from src.fetch_news import fetch_top_headlines
from src.embed_rank import rank_articles_by_interest


def run_pipeline():
    print("Fetching news...")
    articles = fetch_top_headlines(country="us", page_size=10)

    print(f"Fetched {len(articles)} articles.")

    user_interest = "Artificial Intelligence and technology innovation"

    top_articles = rank_articles_by_interest(
        articles,
        user_interest=user_interest,
        top_k=3
    )

    print(f"\nSelected {len(top_articles)} articles for summarization.")
