# 📰 AI News English Study
> **LLM 기반 개인화 뉴스 요약 및 브라우저 사이드 시맨틱 검색 엔진**
> 
> 사용자의 영어 수준(CEFR 레벨, 유럽언어기준)에 맞춰 뉴스를 재구성하고, 단순 키워드가 아닌 '의미' 단위로 콘텐츠를 탐색하는 AI 학습 플랫폼입니다.

[![Web Site](https://img.shields.io/badge/Visit-Live%20Demo-blue?style=for-the-badge&logo=googlechrome)](https://gksruf293.github.io/news_summarizer/)

---

## 🎯 Project Purpose (프로젝트 필요성)
* **난이도 장벽 해소**: 매일 업데이트되는 영문 뉴스 속에서 자신의 수준에 맞는 콘텐츠를 찾기 어려운 학습자를 위해, 동일한 정보를 세 가지 난이도로 치환하여 제공합니다.
* **학습 효율 극대화**: 동일한 사건을 단문(Level 1)부터 복합적인 학술 문장(Level 3)까지 단계적으로 접하며 자연스러운 문법 확장을 유도합니다.
* **지능형 뉴스 탐색**: 'Apple' 검색 시 과일이 아닌 'IT 기업' 관련 뉴스를 문맥적으로 정확히 찾아주는 시맨틱 검색 경험을 제공합니다.

---

## 🛠 Tech Stack & Why (기술 스택 및 선정 이유)

### **1. AI & LLM Pipeline**
* **GPT-4o-mini (OpenAI)**: 비용 효율성을 유지하면서 정교한 프롬프트 엔지니어링을 통해 **초등(3줄/A1), 중등(5줄/B2), 고등(7줄/C1)** 수준의 언어 치환(Paraphrasing)을 수행합니다.
* **HuggingFace Inference API**: `all-MiniLM-L6-v2` 모델을 활용해 뉴스 데이터의 **고차원 벡터 임베딩**을 생성, 서버 부하 없이 고성능 시맨틱 검색의 기반을 마련했습니다.

### **2. Frontend & Edge AI**
* **Transformers.js (Xenova)**: Python 환경의 모델을 브라우저(Web Worker)에서 직접 실행합니다. 서버 비용 없이 사용자의 로컬 환경에서 **Cosine Similarity 연산**을 수행하여 즉각적인 검색 결과를 구현했습니다.
* **Vanilla JS & Mobile First**: 라이브러리 의존성을 최소화하여 초기 로딩 속도를 최적화하였으며, 모바일 학습 환경에 최적화된 반응형 UI를 채택했습니다.

### **3. Data Automation (MLOps)**
* **GitHub Actions (CI/CD)**: 매일 정해진 시간에 Python 파이프라인을 자동 실행합니다. [뉴스 수집 → LLM 요약 → 임베딩 생성 → JSON 업데이트]로 이어지는 **End-to-End 자동화 프로세스**를 구축했습니다.

---

## 🧠 Key Features & Technical Challenges

### **1. Adaptive Multi-Level Summarization **
단순 요약을 넘어 교육적 효과를 극대화하기 위해 레벨별 가이드라인을 엄격히 적용했습니다.
* **Level 1 (Elementary)**: 핵심 정보 중심의 단문 3줄 (기초 어휘 위주)
* **Level 2 (Middle)**: 문장 간 연결성을 강조한 중문 5줄 (중급 표현 포함)
* **Level 3 (High)**: 학술적 어휘와 복잡한 구문을 포함한 7줄 (고급 독해용)

### **2. Client-side Semantic Search Engine**
기존의 키워드 매칭 방식이 가진 문맥 파악의 한계를 극복했습니다.
* **Challenge**: 웹 브라우저 내 대량의 벡터 연산 시 발생하는 성능 저하.
* **Solution**: 가벼운 `all-MiniLM` 모델 사용 및 효율적인 데이터 구조 설계를 통해 100개 이상의 기사에 대한 유사도 연산을 0.1초 내외로 단축했습니다.

---

## 📈 System Architecture
1. **Data Ingestion**: NewsAPI를 통해 실시간 카테고리별 뉴스 수집.
2. **LLM Processing**: OpenAI API를 통한 레벨별 요약 및 한국어 번역 페어 생성.
3. **Vectorization**: HuggingFace 모델로 검색용 고차원 벡터 추출 및 JSON 저장.
4. **Static Hosting**: GitHub Pages를 통해 서버리스 환경에서 정적 데이터 및 AI 모델 서빙.

---

## 🔗 Link
* **Live Demo**: [https://gksruf293.github.io/news_summarizer/](https://gksruf293.github.io/news_summarizer/)
* **Developer**: 임한결 (AI Developer / RAG & Computer Vision Specialist)
