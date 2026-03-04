import os
import json
import time
from datetime import datetime
import requests
from openai import OpenAI
from fetch_news import fetch_top_headlines

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HF_TOKEN = os.getenv("HF_TOKEN")

# ✅ 410 에러 해결: 최신 router 엔드포인트와 feature-extraction 경로를 결합합니다.
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://router.huggingface.co/models/{MODEL_ID}"

CATEGORY_LIST = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def query_hf_embedding(text):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "x-use-cache": "true"
    }
    # 라우터 방식에서는 payload 형식을 단순화하는 것이 좋습니다.
    payload = {"inputs": text[:1000]}
    
    for i in range(3):
        try:
            # wait_for_model을 헤더나 파라미터 대신 로직으로 처리하거나, 필요시 payload에 포함
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res = response.json()
                # 정상 응답이 리스트 형태인지 확인 후 반환
                return res[0] if isinstance(res, list) else res
            
            elif response.status_code == 503 or response.status_code == 429:
                print(f"⌛ 모델 로딩 중 또는 요청 과부하... {i+1}차 대기 (20초)")
                time.sleep(20)
                continue
            else:
                print(f"⚠️ API 오류 {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"❌ 네트워크 에러: {e}")
        time.sleep(2)
    return None

def generate_multi_summaries(text):
    """안정적인 1회 호출 요약"""
    if not text or len(text) < 30:
        return {k: {"en": "No content", "ko": "내용 없음"} for k in ["elementary", "middle", "high"]}
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Teacher mode. Summarize in 2 sentences. Format: English ||| Korean"},
                {"role": "user", "content": text[:1200]}
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
    print(f"🚀 파이프라인 시작 (Endpoint Updated): {today_str}")

    # 1. 시맨틱 검색용 임베딩 생성 (20개)
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
            
    # 2. 카테고리별 뉴스 데이터 생성
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

    # 3. 데이터 저장
    for p in [f"docs/data/{today_str}", "docs/data/latest"]:
        os.makedirs(p, exist_ok=True)
        with open(f"{p}/category.json", "w", encoding="utf-8") as f:
            json.dump(category_results, f, ensure_ascii=False)
        with open(f"{p}/embedding.json", "w", encoding="utf-8") as f:
            json.dump(embedding_results, f, ensure_ascii=False)
            
    print(f"\n✨ 전체 완료! 소요시간: {int(time.time() - start_time)}초 | 임베딩 성공: {len(embedding_results)}개")

if __name__ == "__main__":
    run_pipeline()
