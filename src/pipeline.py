import os
import json
import time
from datetime import datetime
from huggingface_hub import InferenceClient
from openai import OpenAI
from src.fetch_news import fetch_top_headlines

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
hf_client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
# 요청하신 5~7개 카테고리 유지
CATEGORY_LIST = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def get_embedding(text):
    try:
        embedding = hf_client.feature_extraction(text[:1000], model=MODEL_ID)
        return embedding.tolist() if hasattr(embedding, "tolist") else embedding
    except Exception as e:
        print(f"⚠️ HF API 에러: {e}")
        return None

def generate_multi_summaries(title, description):
    """제목과 본문을 조합하여 요약 생성 (No Content 방지)"""
    # 원본 텍스트가 너무 짧으면 요약 대신 제목과 설명을 그대로 활용
    source_text = description if description and len(description) > 50 else title
    
    if not source_text or len(source_text) < 10:
        return {k: {"en": title, "ko": "내용 요약이 제공되지 않는 기사입니다."} for k in ["elementary", "middle", "high"]}

    try:
        resp = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful teacher. Summarize in 2 short sentences. Format: English ||| Korean"},
                {"role": "user", "content": source_text[:1200]}
            ],
            temperature=0.3
        )
        res = resp.choices[0].message.content.strip()
        if "|||" in res:
            en, ko = res.split("|||")
            return {k: {"en": en.strip(), "ko": ko.strip()} for k in ["elementary", "middle", "high"]}
    except Exception as e:
        print(f"⚠️ 요약 생성 에러: {e}")
    
    # 에러 발생 시 fallback
    return {k: {"en": title, "ko": "요약 생성 중 오류가 발생했습니다."} for k in ["elementary", "middle", "high"]}

def run_pipeline():
    start_time = time.time()
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 파이프라인 시작 (100개 데이터 목표): {today_str}")

    all_collected_articles = []
    category_results = {}

    # 1. 각 카테고리별로 20개씩 수집
    for cat in CATEGORY_LIST:
        print(f"--- {cat} 카테고리 수집 중 ---")
        articles = fetch_top_headlines(category=cat, page_size=20)
        processed = []
        
        for art in articles:
            # 요약 및 데이터 정제
            summaries = generate_multi_summaries(art['title'], art.get('description'))
            entry = {
                "title": art["title"],
                "url": art["url"],
                "image": art.get("urlToImage"),
                "summaries": summaries,
                "description": art.get('description', '') # 검색 품질을 위해 원문 보관
            }
            processed.append(entry)
            all_collected_articles.append(entry)
            print("✅", end="", flush=True)
        
        category_results[cat] = processed
        print(f"\n{cat} 완료 ({len(processed)}개)")

    # 2. 전체 데이터 임베딩 생성 (시맨틱 검색용 100개 목표)
    print("\n--- 시맨틱 임베딩 생성 시작 (Top 100) ---")
    embedding_results = []
    # 중복 제거 및 최대 100개 선정
    unique_articles = {a['url']: a for a in all_collected_articles}.values()
    target_articles = list(unique_articles)[:100]

    for art in target_articles:
        # 제목과 설명을 합쳐서 문맥 강화
        search_text = f"{art['title']}. {art['description']}"
        emb = get_embedding(search_text)
        if emb:
            art['embedding'] = emb
            embedding_results.append(art)
            print("💎", end="", flush=True)

    # 3. 저장
    for p in [f"docs/data/{today_str}", "docs/data/latest"]:
        os.makedirs(p, exist_ok=True)
        with open(f"{p}/category.json", "w", encoding="utf-8") as f:
            json.dump(category_results, f, ensure_ascii=False)
        with open(f"{p}/embedding.json", "w", encoding="utf-8") as f:
            json.dump(embedding_results, f, ensure_ascii=False)
            
    print(f"\n✨ 완료! 소요시간: {int(time.time() - start_time)}초")
    print(f"📊 총 수집: {len(all_collected_articles)} | 임베딩 성공: {len(embedding_results)}개")

if __name__ == "__main__":
    run_pipeline()
