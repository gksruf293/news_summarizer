import os
import json
import time
from src.fetch_news import fetch_by_category, fetch_everything, get_full_text
from src.embed_rank import get_embedding

# 수집할 카테고리 목록
CATEGORY_LIST = [
    "business", "entertainment", "general",
    "health", "science", "sports", "technology"
]

def save_json(path, data):
    """JSON 데이터를 파일로 저장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_pipeline():
    # 1️⃣ Category 뉴스 수집 (메인 페이지용 간략 정보)
    category_data = {}
    for cat in CATEGORY_LIST:
        print(f"Fetching category: {cat}")
        try:
            articles = fetch_by_category(category=cat, page_size=12) # 조금 넉넉히 수집
            category_data[cat] = [
                {
                    "title": a["title"], 
                    "description": a["description"], 
                    "url": a["url"],
                    "image": a.get("image"), # 이미지 추가
                    "source": a.get("source"), # 출처 추가
                    "publishedAt": a.get("publishedAt") # 날짜 추가
                } 
                for a in articles
            ]
        except Exception as e:
            print(f"Failed to fetch category {cat}: {e}")
            category_data[cat] = []

    save_json("docs/data/category.json", category_data)
    print("--- ✅ Saved category news! ---\n")

    # 2️⃣ Interest 뉴스 수집 (검색 및 추천용 임베딩 포함)
    query = "Artificial Intelligence and technology innovation"
    print(f"Fetching everything for interest: {query}")
    
    # fetch_news.py에서 정제된 기사 목록을 가져옴
    raw_articles = fetch_everything(query=query, page_size=50)

    embedding_data = []
    seen_urls = set() # 중복 방지

    for i, art in enumerate(raw_articles):
        # 중복 제거 (이미 위에서 처리되었지만 파이프라인에서 한 번 더 검증)
        if art["url"] in seen_urls:
            continue
        
        print(f"[{i+1}/{len(raw_articles)}] Processing: {art['title'][:40]}...")

        # 2-A. 본문 추출 시도 (get_full_text 활용)
        full_text = get_full_text(art["url"])
        
        # 2-B. 임베딩할 텍스트 결정 (본문 -> 설명 -> 제목 순)
        # 본문이 너무 짧으면(예: 200자 미만) 설명글을 사용
        content_to_embed = full_text if len(full_text) > 200 else art["text"]
        
        if not content_to_embed or len(content_to_embed.strip()) < 20:
            continue

        try:
            # 임베딩 생성
            emb = get_embedding(content_to_embed)
            
            embedding_data.append({
                "title": art["title"],
                "description": art["description"],
                "url": art["url"],
                "image": art.get("image"),
                "source": art.get("source"),
                "publishedAt": art.get("publishedAt"),
                "full_text": full_text[:2000], # 용량 관리를 위해 본문은 일부만 저장
                "embedding": emb
            })
            seen_urls.add(art["url"])
            
            # API 할당량 및 서버 부하 방지를 위한 미세 지연
            time.sleep(0.1)
            
        except Exception as e:
            print(f"   ❌ Failed to get embedding for {art['url']}: {e}")
            continue

    save_json("docs/data/embedding.json", embedding_data)
    print(f"\n--- ✅ Saved {len(embedding_data)} interest embeddings! ---")

if __name__ == "__main__":
    run_pipeline()
