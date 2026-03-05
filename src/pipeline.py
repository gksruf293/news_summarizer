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
CATEGORY_LIST = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def get_embedding(text):
    try:
        embedding = hf_client.feature_extraction(text[:1000], model=MODEL_ID)
        return embedding.tolist() if hasattr(embedding, "tolist") else embedding
    except Exception as e:
        print(f"⚠️ HF API 에러: {e}")
        return None

def generate_multi_summaries(title, description, retries=3):
    """레벨별 요약 생성 (서버 에러 시 최대 3번 재시도)"""
    source_text = description if description and len(description) > 50 else title
    
    if not source_text or len(source_text) < 10:
        msg = {"en": title, "ko": "내용 요약이 제공되지 않는 기사입니다."}
        return {k: msg for k in ["elementary", "middle", "high"]}

    for i in range(retries):
        try:
            resp = client_openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """You are a professional English teacher. 
                    Summarize the given news into 3 distinct levels:
                    - Level 1 (Elementary): Exactly 3 short sentences. Basic vocabulary (A1).
                    - Level 2 (Middle): Exactly 5 sentences. Intermediate vocabulary (B1-B2).
                    - Level 3 (High): Exactly 7 sentences. Advanced vocabulary (C1).
                    Format: Level X: [English] ||| [Korean]"""},
                    {"role": "user", "content": source_text[:1200]}
                ],
                temperature=0.4
            )
            
            content = resp.choices[0].message.content.strip()
            lines = [line for line in content.split('\n') if "|||" in line]
            
            levels = ["elementary", "middle", "high"]
            summaries = {}
            
            for idx, line in enumerate(lines[:3]):
                clean_line = line.split(":", 1)[-1] if ":" in line else line
                en, ko = clean_line.split("|||")
                summaries[levels[idx]] = {
                    "en": en.strip().replace(". ", ".<br>"), 
                    "ko": ko.strip().replace(". ", ".<br>")
                }
            return summaries

        except Exception as e:
            # 500 에러 등이 발생했을 때 잠시 대기 후 재시도
            print(f"\n⚠️ 요약 생성 에러 (시도 {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(2) # 2초 대기 후 재시도
            else:
                print(f"❌ {retries}번 시도 후 결국 실패: {title[:30]}...")
    
    # 모든 재시도 실패 시 fallback
    fallback = {"en": title, "ko": "현재 요약을 생성할 수 없습니다. 원문 링크를 확인해 주세요."}
    return {k: fallback for k in ["elementary", "middle", "high"]}

def run_pipeline():
    start_time = time.time()
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 파이프라인 시작: {today_str}")

    all_collected_articles = []
    category_results = {}

    for cat in CATEGORY_LIST:
        print(f"\n--- {cat} 카테고리 수집 중 ---")
        articles = fetch_top_headlines(category=cat, page_size=20)
        processed = []
        for art in articles:
            summaries = generate_multi_summaries(art['title'], art.get('description'))
            entry = {
                "title": art["title"],
                "url": art["url"],
                "image": art.get("urlToImage"),
                "summaries": summaries,
                "description": art.get('description', '')
            }
            processed.append(entry)
            all_collected_articles.append(entry)
            print("✅", end="", flush=True)
        category_results[cat] = processed

    print("\n\n--- 시맨틱 임베딩 생성 시작 ---")
    unique_articles = {a['url']: a for a in all_collected_articles}.values()
    target_articles = list(unique_articles)[:100]
    embedding_results = []

    for art in target_articles:
        search_text = f"{art['title']}. {art['description']}"
        emb = get_embedding(search_text)
        if emb:
            art['embedding'] = emb
            embedding_results.append(art)
            print("💎", end="", flush=True)

    for p in [f"docs/data/{today_str}", "docs/data/latest"]:
        os.makedirs(p, exist_ok=True)
        with open(f"{p}/category.json", "w", encoding="utf-8") as f:
            json.dump(category_results, f, ensure_ascii=False)
        with open(f"{p}/embedding.json", "w", encoding="utf-8") as f:
            json.dump(embedding_results, f, ensure_ascii=False)
            
    print(f"\n✨ 완료! 소요시간: {int(time.time() - start_time)}초")

if __name__ == "__main__":
    run_pipeline()
