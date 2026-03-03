import os
import json
import time
from datetime import datetime
import requests
from openai import OpenAI  # 최신 v1.0+ 방식
from fetch_news import fetch_by_category, fetch_everything, get_full_text

# 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

CATEGORY_LIST = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

def query_hf_embedding(text):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    for _ in range(3):
        try:
            response = requests.post(HF_API_URL, headers=headers, json={"inputs": text}, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                time.sleep(15)
                continue
        except:
            pass
    return None

def generate_multi_summaries(text):
    """최신 OpenAI SDK(v1.0+)를 사용한 3단계 요약"""
    prompts = {
        "elementary": "초등학생이 이해하기 쉽게 아주 쉬운 단어로 2줄 요약해줘.",
        "middle": "중학생 수준으로 핵심 용어를 설명하며 3줄 내외로 요약해줘.",
        "high": "고등학생 이상의 수준으로 논리적이고 전문적인 문체로 상세히 요약해줘."
    }
    summaries = {}
    
    if not text or len(text.strip()) < 100:
        return {k: "본문 내용이 부족하여 요약할 수 없습니다." for k in prompts}

    for level, prompt in prompts.items():
        try:
            # 최신 API 호출 방식
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "너는 뉴스 교육 전문가야. 반드시 한국어로 답변해."},
                    {"role": "user", "content": f"{prompt}\n\n내용: {text[:3500]}"}
                ],
                temperature=0.3
            )
            summaries[level] = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ OpenAI API 에러 ({level}): {e}")
            summaries[level] = "요약 생성 중 오류가 발생했습니다."
    return summaries

def run_pipeline():
    # 0️⃣ 날짜 설정
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Running Pipeline for Date: {today_str}")

    # 1️⃣ 카테고리 뉴스 수집 및 요약
    final_category_data = {}
    for cat in CATEGORY_LIST:
        print(f"--- Processing Category: {cat} ---")
        articles = fetch_by_category(category=cat, page_size=5)
        processed = []
        for art in articles:
            full_text = get_full_text(art["url"])
            # 본문 추출 실패 시 description이라도 사용
            target_text = full_text if len(full_text) > 200 else art.get("description", "")
            
            print(f"Summarizing: {art['title'][:40]}...")
            summaries = generate_multi_summaries(target_text)
            
            processed.append({
                "title": art["title"],
                "url": art["url"],
                "image": art.get("image"),
                "source": art.get("source"),
                "publishedAt": art.get("publishedAt"),
                "summaries": summaries
            })
        final_category_data[cat] = processed

    # 2️⃣ 검색용 임베딩 생성 (50개)
    print("\n--- Generating Search Embeddings ---")
    interest_news = fetch_everything(query="AI technology innovation", page_size=50)
    embedding_data = []
    for art in interest_news:
        emb = query_hf_embedding(f"{art['title']}. {art.get('description', '')}")
        if emb:
            embedding_data.append({
                "title": art["title"],
                "url": art["url"],
                "description": art.get("description"),
                "image": art.get("image"),
                "embedding": emb
            })

    # 3️⃣ 데이터 저장 (날짜별 폴더 및 최신 폴더)
    data_paths = [f"docs/data/{today_str}", "docs/data/latest"]
    for path in data_paths:
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/category.json", "w", encoding="utf-8") as f:
            json.dump(final_category_data, f, ensure_ascii=False, indent=2)
        with open(f"{path}/embedding.json", "w", encoding="utf-8") as f:
            json.dump(embedding_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Pipeline Completed! Data saved in docs/data/{today_str}")

def generate_multi_summaries(text):
    """영문 요약과 한글 번역을 동시에 생성"""
    prompts = {
        "elementary": "Summarize in 2 simple sentences for a child. (A1 level)",
        "middle": "Summarize in 3 clear sentences with key vocabulary. (B1 level)",
        "high": "Summarize in a logical and professional manner. (C1 level)"
    }
    summaries = {}
    
    if not text or len(text.strip()) < 100:
        return {k: {"en": "Content too short.", "ko": "내용이 너무 짧습니다."} for k in prompts}

    for level, prompt in prompts.items():
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an English teacher. Summarize the news in English and provide its Korean translation. Format: English text ||| Korean translation"},
                    {"role": "user", "content": f"{prompt}\n\nContent: {text[:3500]}"}
                ],
                temperature=0.3
            )
            res_text = response.choices[0].message.content.strip()
            # '|||' 구분자로 영문과 한글 분리
            if "|||" in res_text:
                en, ko = res_text.split("|||")
                summaries[level] = {"en": en.strip(), "ko": ko.strip()}
            else:
                summaries[level] = {"en": res_text, "ko": "(번역 준비 중)"}
        except Exception as e:
            summaries[level] = {"en": "Error occurred.", "ko": "오류 발생"}
            
    return summaries

if __name__ == "__main__":
    run_pipeline()
