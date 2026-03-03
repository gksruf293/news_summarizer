# src/pipeline.py

import os
import json
from src.fetch_news import fetch_by_category, fetch_everything
from src.embed_rank import get_embedding

CATEGORY_LIST = [
    "business", "entertainment", "general",
    "health", "science", "sports", "technology"
]

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_pipeline():
    # 1️⃣ Category 뉴스 (top 10, 임베딩 없음)
    category_data = {}
    for cat in CATEGORY_LIST:
        print(f"Fetching category: {cat}")
        articles = fetch_by_category(category=cat, page_size=10)
        category_data[cat] = [{"title": a["title"], "description": a["description"], "url": a["url"]} for a in articles]

    save_json("docs/data/category.json", category_data)
    print("Saved category news!")

    # 2️⃣ Interest 뉴스 (everything 50개 + embedding)
    query = "Artificial Intelligence and technology innovation"  # 기본 interest
    print(f"Fetching everything for interest: {query}")
    articles = fetch_everything(query=query, page_size=50)

    embedding_data = []
    for art in articles:
        emb = get_embedding(art["text"])
        embedding_data.append({
            "title": art["title"],
            "description": art["description"],
            "url": art["url"],
            "embedding": emb
        })

    save_json("docs/data/embedding.json", embedding_data)
    print("Saved interest embeddings!")
