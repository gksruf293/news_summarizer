# src/embed_rank.py

import os
import requests
import numpy as np
from typing import List, Dict


OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


def _get_openai_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    return api_key


def get_embedding(text: str) -> List[float]:
    """
    Call OpenAI embedding API for a single text input.
    """
    url = "https://api.openai.com/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {_get_openai_key()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENAI_EMBEDDING_MODEL,
        "input": text
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["data"][0]["embedding"]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def rank_articles_by_interest(
    articles: List[Dict],
    user_interest: str,
    top_k: int = 3
) -> List[Dict]:
    """
    Rank articles by semantic similarity to user_interest.
    """

    print("Generating embedding for user interest...")
    user_embedding = get_embedding(user_interest)

    scored_articles = []

    for article in articles:
        article_text = article["text"]

        print(f"Embedding article: {article['title'][:50]}...")
        article_embedding = get_embedding(article_text)

        similarity = cosine_similarity(user_embedding, article_embedding)

        scored_articles.append((similarity, article))

    # sort descending
    scored_articles.sort(key=lambda x: x[0], reverse=True)

    top_articles = [article for similarity, article in scored_articles[:top_k]]

    print("\nTop ranked articles:")
    for sim, art in scored_articles[:top_k]:
        print(f"Score: {sim:.4f} | {art['title']}")

    return top_articles
