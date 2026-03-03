# src/build_everything_embeddings.py

import os
import json
import requests
from typing import List, Dict
from src.fetch_news import fetch_everything
from src.embed_rank import get_embedding

OUTPUT_PATH = "docs/data/everything_embeddings.json"
TARGET_ARTICLE_COUNT = 500


def collect_articles(target_count: int = 500) -> List[Dict]:
    """
    Collect articles using NewsAPI everything endpoint.
    """
    print("Collecting articles from NewsAPI (everything)...")

    articles = []
    page = 1

    while len(articles) < target_count:
        print(f"Fetching page {page}...")

        batch = fetch_everything(
            query="technology OR AI OR business OR science OR sports",
            language="en",
            page_size=100,
            page=page
        )

        if not batch:
            break

        articles.extend(batch)
        page += 1

    print(f"Collected {len(articles)} articles.")
    return articles[:target_count]


def build_embeddings(articles: List[Dict]) -> List[Dict]:
    """
    Generate embeddings for all articles.
    """
    embedded_data = []

    for idx, article in enumerate(articles):
        try:
            print(f"[{idx+1}/{len(articles)}] Embedding: {article['title'][:60]}")

            text = article.get("text") or article.get("description") or article["title"]

            embedding = get_embedding(text)

            embedded_data.append({
                "title": article["title"],
                "url": article["url"],
                "source": article.get("source", ""),
                "summary": article.get("description", ""),
                "category": article.get("category", "unknown"),
                "embedding": embedding
            })

        except Exception as e:
            print(f"Error embedding article: {e}")
            continue

    return embedded_data


def save_embeddings(data: List[Dict]):
    os.makedirs("docs/data", exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)

    print(f"Saved embeddings to {OUTPUT_PATH}")


def main():
    articles = collect_articles(TARGET_ARTICLE_COUNT)
    embedded = build_embeddings(articles)
    save_embeddings(embedded)


if __name__ == "__main__":
    main()
