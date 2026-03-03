import os
import json
import time
import requests
import openai
from fetch_news import fetch_by_category, fetch_everything, get_full_text

# API 키 설정 (GitHub Secrets에서 자동 주입)
openai.api_key = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

CATEGORY_LIST = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def query_hf_embedding(text):
    """HuggingFace Inference API를 통한 벡터 변환"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    # 모델이 로드 중일 경우를 대비해 retry 로직 포함
    for _ in range(3):
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": text})
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503: # Model loading
            time.sleep(15)
            continue
    return None

def generate_multi_summaries(text):
    """OpenAI GPT를 이용한 초/중/고 3단계 요약"""
    prompts = {
        "elementary": "초등학생이 이해하기 쉽게 아주 쉬운 단어와 비유를 들어 2줄로 요약해줘.",
        "middle": "중학생 수준으로 핵심 용어를 설명하며 3줄 내외로 요약해줘.",
        "high": "고등학생 이상의 수준으로 논리적이고 전문적인 문체로 상세히 요약해줘."
    }
    summaries = {}
    for level, prompt in prompts.items():
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 뉴스 교육 콘텐츠 제작자야. 반드시 한국어로 응답해."},
                    {"role": "user", "content": f"{prompt}\n\n내용: {text[:3000]}"}
                ],
                temperature=0.5
            )
            summaries[level] = response.choices[0].message.content
        except:
            summaries[level] = "요약을 생성하는 중 오류가 발생했습니다."
    return summaries

def run_pipeline():
    # 1️⃣ 카테고리 뉴스: 다층 요약 포함 (카테고리당 5개)
    final_category_data = {}
    for cat in CATEGORY_LIST:
        print(f"--- Processing Category: {cat} ---")
        articles = fetch_by_category(category=cat, page_size=5)
        processed_articles = []
        for art in articles:
            full_text = get_full_text(art["url"])
            # 403 Forbidden 등으로 본문 수집 실패 시 description 활용
            target_text = full_text if len(full_text) > 200 else art["text"]
            
            print(f"Summarizing: {art['title'][:40]}...")
            summaries = generate_multi_summaries(target_text)
            
            processed_articles.append({
                "title": art["title"],
                "url": art["url"],
                "image": art.get("image"),
                "source": art.get("source"),
                "publishedAt": art.get("publishedAt"),
                "summaries": summaries
            })
        final_category_data[cat] = processed_articles

    # 2️⃣ Interest 뉴스: 검색용 임베딩 포함 (50개)
    print("\n--- Generating Search Embeddings ---")
    interest_news = fetch_everything(query="AI technology innovation future", page_size=50)
    embedding_data = []
    for art in interest_news:
        # 검색 정확도를 위해 '제목 + 설명' 기반 임베딩
        embedding = query_hf_embedding(f"{art['title']}. {art['description']}")
        if embedding:
            embedding_data.append({
                "title": art["title"],
                "url": art["url"],
                "description": art["description"],
                "image": art.get("image"),
                "embedding": embedding
            })
    
    # 데이터 저장 (github.io용 docs 폴더)
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/category.json", "w", encoding="utf-8") as f:
        json.dump(final_category_data, f, ensure_ascii=False, indent=2)
    with open("docs/data/embedding.json", "w", encoding="utf-8") as f:
        json.dump(embedding_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_pipeline()
