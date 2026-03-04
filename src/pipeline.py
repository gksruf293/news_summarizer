import os
import json
import time
from datetime import datetime
from huggingface_hub import InferenceClient
from openai import OpenAI
from fetch_news import fetch_top_headlines

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

def generate_multi_summaries(title, description):
    """레벨별(3, 5, 7줄) 확실한 차이를 둔 요약 생성"""
    source_text = description if description and len(description) > 50 else title
    
    if not source_text or len(source_text) < 10:
        msg = {"en": title, "ko": "내용 요약이 제공되지 않는 기사입니다."}
        return {k: msg for k in ["elementary", "middle", "high"]}

    try:
        resp = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a professional English teacher. 
                Summarize the given news into 3 distinct levels:
                
                - Level 1 (Elementary): Exactly 3 short sentences. Use very simple words (A1 level).
                - Level 2 (Middle): Exactly 5 sentences. Use intermediate vocabulary (B1-B2 level).
                - Level 3 (High): Exactly 7 sentences. Use advanced academic vocabulary and complex structures (C1 level).
                
                Format each level exactly as:
                Level X: [English Summary] ||| [Korean Translation]"""},
                {"role": "user", "content": source_text[:1200]}
            ],
            temperature=0.4
        )
        
        content = resp.choices[0].message.content.strip()
        lines = [line for line in content.split('\n') if "|||" in line]
        
        levels = ["elementary", "middle", "high"]
        summaries = {}
        
        for i, line in enumerate(lines[:3]):
            clean_line = line.split(":", 1)[-1] if ":" in line else line
            en, ko = clean_line.split("|||")
            # <br> 태그를 넣어 웹에서 줄바꿈이 보이도록 처리
            summaries[levels[i]] = {
                "en": en.strip().replace(". ", ".<br>"), 
                "ko": ko.strip().replace(". ", ".<br>")
            }
            
        return summaries
    except Exception as e:
        print(f"⚠️ 요약 생성 에러: {e}")
        fallback = {"en": title, "ko": "요약 생성 중 오류가 발생했습니다."}
        return {k: fallback for k in ["elementary", "middle", "high"]}

def run_pipeline():
    start_time = time.time()
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 파이프라인 시작: {today_str}")

    all_collected_articles = []
    category_results = {}

    for cat in CATEGORY_LIST:
        print(f"--- {cat} 카테고리 수집 중 ---")
        articles = fetch_top_headlines(category=cat, page_size=20)
        processed = []
        for art in articles:
            summaries = generate_multi_summaries(art['title'], art.get('description'))
            entry = {
                "title": art["title"],
                "url": art["url"],
                "image": art.get("urlToImage"), # null일 수 있음
                "summaries": summaries,
                "description": art.get('description', '')
            }
            processed.append(entry)
            all_collected_articles.append(entry)
            print("✅", end="", flush=True)
        category_results[cat] = processed
        print(f"\n{cat} 완료 ({len(processed)}개)")

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
            
    print(f"\n✨ 완료! 총 데이터: {len(embedding_results)}개")

if __name__ == "__main__":
    run_pipeline()
