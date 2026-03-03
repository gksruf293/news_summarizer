import requests
import os

API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2"

def fetch_top_headlines(category=None, country="us", page_size=100):
    """
    /top-headlines 엔드포인트를 사용하여 신뢰도 높은 주요 뉴스를 가져옵니다.
    category가 None이면 전체 주요 뉴스를, 지정되면 해당 카테고리 뉴스를 가져옵니다.
    """
    url = f"{BASE_URL}/top-headlines"
    params = {
        "country": country,
        "pageSize": page_size,
        "apiKey": API_KEY
    }
    if category:
        params["category"] = category
        
    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            print(f"⚠️ API Error: {data.get('message')}")
            return []
    except Exception as e:
        print(f"❌ Fetch Error: {e}")
        return []

def get_full_text(url):
    """뉴스 본문 추출"""
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except:
        return ""
