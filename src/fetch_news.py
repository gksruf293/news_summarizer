import os
import requests
from typing import List, Dict

NEWS_API_URL = "https://newsapi.org/v2"

# NewsAPI에서 공식 지원하는 category만 허용
ALLOWED_CATEGORIES = {
    "business",
    "entertainment",
    "general",
    "health",
    "science",
    "sports",
    "technology"
}

def _get_api_key() -> str:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY not found in environment variables.")
    return api_key

def fetch_by_category(
    category: str,
    country: str = "us",
    page_size: int = 30
) -> List[Dict]:
    """
    Fetch articles only from allowed NewsAPI categories.
    """

    if category not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"Invalid category: {category}. Must be one of {ALLOWED_CATEGORIES}"
        )

    url = f"{NEWS_API_URL}/top-headlines"

    # 1️⃣ CORS 에러 방지를 위한 핵심 설정: User-Agent 헤더 추가
    # 2️⃣ 보안을 위해 API Key를 URL 파라미터가 아닌 헤더로 전달
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Api-Key": _get_api_key()
    }

    params = {
        "country": country,
        "category": category,
        "pageSize": page_size
    }

    try:
        # params에서 apiKey를 제거하고 headers로 전달합니다.
        response = requests.get(url, params=params, headers=headers)
        
        # 에러 메시지가 JSON 형태일 경우 상세히 출력하여 디버깅을 돕습니다.
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

    articles = response.json().get("articles", [])
    return _clean_articles(articles)


def _clean_articles(raw_articles: List[Dict]) -> List[Dict]:
    """
    - Remove articles without title or url
    - Deduplicate by URL
    - Create unified 'text' field for retrieval
    """

    seen_urls = set()
    cleaned = []

    for article in raw_articles:
        title = article.get("title")
        description = article.get("description")
        url = article.get("url")

        # [Removed]로 표시된 무효한 기사 제외
        if not title or not url or "[Removed]" in title:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        # 요약 및 임베딩을 위해 제목과 본문 설명을 합친 텍스트 필드 생성
        combined_text = f"{title}. {description or ''}"

        cleaned.append({
            "title": title,
            "description": description,
            "url": url,
            "source": article.get("source", {}).get("name"),
            "publishedAt": article.get("publishedAt"),
            "text": combined_text
        })

    return cleaned
