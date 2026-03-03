import os
import requests
from typing import List, Dict
from newspaper import Article

NEWS_API_URL = "https://newsapi.org/v2"

# NewsAPI에서 공식 지원하는 category 목록
ALLOWED_CATEGORIES = {
    "business", "entertainment", "general", 
    "health", "science", "sports", "technology"
}

def _get_common_headers() -> Dict:
    """
    CORS 에러를 방지하고 서버 간 통신임을 명시하기 위한 공통 헤더
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY가 환경 변수에 설정되지 않았습니다.")
    
    return {
        # 브라우저가 아닌 서버 요청임을 명시하여 CORS 제한 회피
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Api-Key": api_key
    }

def fetch_by_category(category: str, country: str = "us", page_size: int = 30) -> List[Dict]:
    """
    NewsAPI의 /top-headlines 엔드포인트에서 카테고리별 뉴스 수집
    """
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"유효하지 않은 카테고리입니다: {category}")

    url = f"{NEWS_API_URL}/top-headlines"
    params = {
        "country": country,
        "category": category,
        "pageSize": page_size
    }

    try:
        response = requests.get(url, params=params, headers=_get_common_headers())
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return _clean_articles(articles)
    except Exception as e:
        print(f"카테고리 뉴스 수집 중 오류 발생 ({category}): {e}")
        return []

def fetch_everything(query: str, language: str = "en", page_size: int = 50, page: int = 1) -> List[Dict]:
    """
    NewsAPI의 /everything 엔드포인트에서 키워드 기반 뉴스 수집
    """
    url = f"{NEWS_API_URL}/everything"
    params = {
        "q": query,
        "language": language,
        "pageSize": page_size,
        "page": page,
        "sortBy": "publishedAt" # 최신순 정렬
    }

    try:
        response = requests.get(url, params=params, headers=_get_common_headers())
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return _clean_articles(articles)
    except Exception as e:
        print(f"Everything 뉴스 수집 중 오류 발생 (쿼리: {query}): {e}")
        return []

def _clean_articles(raw_articles: List[Dict]) -> List[Dict]:
    """
    NewsAPI 응답 데이터를 정제하고 중복을 제거함
    """
    seen_urls = set()
    cleaned = []

    for article in raw_articles:
        title = article.get("title")
        url = article.get("url")
        description = article.get("description", "")
        
        # 유효하지 않은 기사 및 삭제된 기사 제외
        if not title or not url or "[Removed]" in title:
            continue

        # URL 중복 제거
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # 텍스트 데이터 구성 (기본적으로는 제목 + 설명을 활용)
        # 나중에 pipeline에서 newspaper3k로 full_text를 보강함
        combined_text = f"{title}. {description if description else ''}"

        cleaned.append({
            "title": title,
            "url": url,
            "description": description,
            "source": article.get("source", {}).get("name"),
            "author": article.get("author"),
            "image": article.get("urlToImage"), # 뉴스 썸네일 이미지
            "publishedAt": article.get("publishedAt"),
            "text": combined_text.strip() # 임베딩 및 요약용 기초 텍스트
        })

    return cleaned

def get_full_text(url: str) -> str:
    """
    newspaper3k를 사용하여 뉴스 URL로부터 전체 본문을 추출
    """
    try:
        article = Article(url)
        # 타임아웃을 설정하여 파이프라인 지연 방지
        article.download(config={'request_timeout': 10})
        article.parse()
        return article.text.strip()
    except Exception as e:
        print(f"본문 추출 실패 ({url}): {e}")
        return ""

from newspaper import Article, Config

def get_full_text(url: str) -> str:
    """
    newspaper3k를 사용하여 뉴스 URL로부터 전체 본문을 추출
    """
    try:
        # 설정을 별도 객체로 생성
        config = Config()
        config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        config.request_timeout = 10

        # Article 생성 시 config 전달
        article = Article(url, config=config)
        article.download() # 여기에 config를 넣으면 에러가 발생합니다.
        article.parse()
        
        return article.text.strip()
    except Exception as e:
        print(f"본문 추출 실패 ({url}): {e}")
        return ""
