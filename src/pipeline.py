import os
import json
import time
from datetime import datetime
import requests
from openai import OpenAI
from src.fetch_news import fetch_top_headlines

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HF_TOKEN = os.getenv("HF_TOKEN")

# 핵심: 알려주신 모델명을 API 경로에 정확히 삽입합니다.
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"

CATEGORY_LIST = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def query_hf_embedding(text):
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    # API가 인식하기 가장 좋은 순수 텍스트 전송 방식
    payload = {"inputs": text[:1000], "options": {"wait_for_model": True}}
    
    for i in range(3):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res = response.json()
                # feature-extraction 결과는 보통 1차원 리스트로 옵니다.
                return res
            elif response.status_code in [503, 404]:
                # 404가 일시적인 경로 문제일 수 있으므로 짧게 재시도
                print(f"⌛ 모델 서버 응답 대기 중 ({response.status_code})... {i+1}차")
                time.sleep(20)
                continue
            else:
                print(f"⚠️ API 오류 {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"❌ 네트워크 에러: {e}")
        time.sleep(2)
    return None

def generate_multi_summaries(text):
    """속도를 위해 1회 호출로 요약 (gpt-4o-mini)"""
    if not text or len(text) < 30:
        return {k: {"en": "No content", "ko": "내용 없음"} for k in ["elementary", "middle", "high"]}
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Teacher mode. Summarize in 2 sentences. Format: English ||| Korean"},
                {"role": "user", "content": text[:1500]}
            ],
            temperature=0.3
        )
        res = resp.choices[0].message.content.strip()
        en, ko = res.split("|||") if "|||" in res else (res, "(번역 중)")
        data = {"en": en.strip(), "ko": ko.strip()}
        return {"elementary": data, "middle": data, "high": data}
    except:
        return {k: {"en": "Error", "ko": "오류"} for k in ["elementary", "middle", "high"]}

def run_pipeline():
    start_time = time.time()
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 파이프라인 시작: {today_str}")

    # 1. 시맨틱 검색 데이터 (20개만 빠르게 진행)
    print("--- 임베딩 생성 시작 ---")
    base_articles = fetch_top_headlines(category="general", page_size=20)
    embedding_results = []
    
    for art in base_articles:
        txt = f"{art['title']}. {art.get('description', '')}"
        emb = query_hf_embedding(txt)
        if emb:
            embedding_results.append({
                "title": art["title"], "url": art["url"], "image": art.get("urlToImage"),
                "embedding": emb, "summaries": generate_multi_summaries(txt)
            })
            print("✅", end="", flush=True)
            
    # 2. 카테고리별 데이터 (본문 크롤링 생략하여 속도 10배 향상)
    category_results = {}
    for cat in CATEGORY_LIST:
        articles = fetch_top_headlines(category=cat, page_size=5)
        processed = []
        for art in articles:
            txt = art.get('description', art['title'])
            processed.append({
                "title": art["title"], "url": art["url"], "image": art.get("urlToImage"),
                "summaries": generate_multi_summaries(txt)
            })
        category_results[cat] = processed

    # 3. 저장
    for p in [f"docs/data/{today_str}", "docs/data/latest"]:
        os.makedirs(p, exist_ok=True)
        with open(f"{p}/category.json", "w", encoding="utf-8") as f:
            json.dump(category_results, f, ensure_ascii=False)
        with open(f"{p}/embedding.json", "w", encoding="utf-8") as f:
            json.dump(embedding_results, f, ensure_ascii=False)
            
    print(f"\n✨ 전체 완료! 소요시간: {int(time.time() - start_time)}초")

if __name__ == "__main__":
    run_pipeline()
