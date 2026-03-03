# src/build_everything_embeddings.py

import os
import json
from typing import List, Dict
from newspaper import Article
from fetch_news import fetch_everything
from embed_rank import get_embedding

OUTPUT_PATH = "docs/data/everything_embeddings.json"
TARGET_ARTICLE_COUNT = 500

def extract_full_text(url: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:5000]  # 너무 길면 잘라
    except Exception as e:
        print(f"Failed to extract full text: {e}")
        return ""


def collect_articles(target_count: int = 500) -> List[Dict]:
    print("Collecting articles from NewsAPI (everything)...")

    articles = []
    page = 1

    while len(articles) < target_count:
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

    return articles[:target_count]


def build_embeddings(articles: List[Dict]) -> List[Dict]:
    embedded_data = []

    for idx, article in enumerate(articles):
        try:
            print(f"[{idx+1}/{len(articles)}] Processing: {article['title'][:60]}")

            full_text = extract_full_text(article["url"])

            base_text = full_text if full_text else (
                article.get("description") or article["title"]
            )

            embedding = get_embedding(base_text)

            embedded_data.append({
                "title": article["title"],
                "url": article["url"],
                "summary": article.get("description", ""),
                "image": article.get("urlToImage", ""),
                "full_text": full_text,
                "embedding": embedding
            })

        except Exception as e:
            print(f"Error: {e}")
            continue

    return embedded_data


def save_embeddings(data: List[Dict]):
    os.makedirs("docs/data", exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def main():
    articles = collect_articles(TARGET_ARTICLE_COUNT)
    embedded = build_embeddings(articles)
    save_embeddings(embedded)


if __name__ == "__main__":
    main()
