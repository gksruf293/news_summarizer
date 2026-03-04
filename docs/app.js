import { pipeline } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.6.0';

let categoryData = {};
let embeddingData = [];
let extractor = null;
let currentSelectedArticle = null;

/**
 * 초기화: AI 모델 로드 및 데이터 페칭
 */
async function init() {
    const container = document.getElementById("results-container");
    const searchBtn = document.getElementById("searchBtn");
    
    if (searchBtn) searchBtn.disabled = true;
    container.innerHTML = `<div class="status-msg">AI 모델 및 뉴스 데이터를 로드 중입니다...</div>`;

    try {
        // 1. 브라우저 로컬 시맨틱 검색을 위한 모델 로드
        extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        console.log("✅ AI Model Loaded");

        // 2. 데이터 로드 (최신 데이터)
        await loadDataByDate('latest');

        if (searchBtn) { 
            searchBtn.disabled = false; 
            searchBtn.innerText = "AI 시맨틱 검색"; 
        }
    } catch (err) {
        console.error("Init Error:", err);
        container.innerHTML = `<div class="error-msg">초기화 중 오류가 발생했습니다. 페이지를 새로고침 해주세요.</div>`;
    }
}

/**
 * 서버에서 JSON 데이터를 가져오는 함수
 */
window.loadDataByDate = async function(date) {
    const container = document.getElementById("results-container");
    try {
        const cacheBust = `?t=${new Date().getTime()}`;
        const [catRes, embRes] = await Promise.all([
            fetch(`./data/${date}/category.json${cacheBust}`),
            fetch(`./data/${date}/embedding.json${cacheBust}`)
        ]);
        
        if (!catRes.ok || !embRes.ok) throw new Error("데이터 파일을 찾을 수 없습니다.");

        categoryData = await catRes.json();
        const embJson = await embRes.json();
        embeddingData = Array.isArray(embJson) ? embJson : [];
        
        console.log(`📊 데이터 로드 완료 | 임베딩: ${embeddingData.length}개`);

        // 초기 화면: 'general' 카테고리 혹은 첫 번째 카테고리 출력
        const firstCat = categoryData['general'] ? 'general' : Object.keys(categoryData)[0];
        renderCards(categoryData[firstCat] || []);

    } catch (err) {
        console.error("Data Load Error:", err);
        container.innerHTML = `<div class="error-msg">데이터 로드 실패: ${err.message}</div>`;
    }
};

/**
 * 시맨틱 검색 실행 함수 (버튼 onclick과 연결)
 */
window.handleSearch = async function() {
    const input = document.getElementById("interestInput");
    const query = input.value.trim();
    
    if (!query) return;
    if (!extractor || embeddingData.length === 0) {
        alert("데이터 로딩 중입니다. 잠시만 기다려주세요.");
        return;
    }

    const container = document.getElementById("results-container");
    container.innerHTML = `<div class="status-msg">'${query}' 관련 뉴스 분석 중...</div>`;

    try {
        // 검색어 임베딩 추출
        const output = await extractor(query, { pooling: 'mean', normalize: true });
        const userVector = Array.from(output.data);

        // 유사도 계산 및 정렬
        const scored = embeddingData.map(art => ({
            ...art,
            score: cosineSimilarity(userVector, art.embedding)
        })).sort((a, b) => b.score - a.score);

        renderCards(scored.slice(0, 12)); // 상위 12개 출력
    } catch (err) {
        console.error("Search Error:", err);
        container.innerHTML = `<div class="error-msg">검색 중 오류가 발생했습니다.</div>`;
    }
};

/**
 * 뉴스 카드 렌더링 함수
 */
function renderCards(articles) {
    const container = document.getElementById("results-container");
    container.innerHTML = "";
    
    if (!articles || articles.length === 0) {
        container.innerHTML = `<div class="status-msg">해당 조건에 맞는 뉴스가 없습니다.</div>`;
        return;
    }

    articles.forEach(art => {
        const card = document.createElement("div");
        card.className = "card";
        
        // 데이터 누락 방지: 설명이 없으면 제목을 미리보기로 사용
        const summaryPreview = art.summaries?.elementary?.en || art.description || art.title || "No preview available.";
        const scoreTag = art.score ? `<span class="score-tag">${Math.round(art.score * 100)}% 관련됨</span>` : '';

        card.innerHTML = `
            ${art.image ? `<img src="${art.image}" onerror="this.style.display='none'">` : ''}
            <div class="card-info">
                ${scoreTag}
                <h3>${art.title}</h3>
                <p>${summaryPreview.slice(0, 120)}...</p>
            </div>
        `;
        card.onclick = () => openModal(art);
        container.appendChild(card);
    });
}

/**
 * 코사인 유사도 계산
 */
function cosineSimilarity(a, b) {
    let dot = 0, nA = 0, nB = 0;
    for (let i = 0; i < a.length; i++) {
        dot += a[i] * b[i];
        nA += a[i] * a[i];
        nB += b[i] * b[i];
    }
    return dot / (Math.sqrt(nA) * Math.sqrt(nB));
}

/**
 * 모달 창 제어
 */
window.openModal = (article) => {
    currentSelectedArticle = article;
    document.getElementById("modal-title").innerText = article.title;
    document.getElementById("modal-link").href = article.url;
    document.getElementById("modal").style.display = "block";
    updateSummaryLevel('elementary');
};

window.closeModal = () => {
    document.getElementById("modal").style.display = "none";
};

window.updateSummaryLevel = (level) => {
    // 요약 데이터가 없을 경우를 대비한 안전 장치
    const summaryData = currentSelectedArticle.summaries?.[level] || { en: "Summary not available.", ko: "요약을 가져올 수 없습니다." };
    
    document.getElementById("summary-text").innerHTML = `
        <div class="english-box" onclick="toggleTranslation()">
            <p class="en-text">${summaryData.en}</p>
            <p class="ko-text" id="ko-translation" style="display:none;">🔍 ${summaryData.ko}</p>
            <small style="color: #3b82f6; display:block; margin-top:10px;">💡 클릭하면 한국어 해석이 나타납니다.</small>
        </div>
    `;
    
    document.querySelectorAll(".level-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.getElementById(`btn-${level}`);
    if (activeBtn) activeBtn.classList.add("active");
};

window.toggleTranslation = () => {
    const ko = document.getElementById("ko-translation");
    if (ko) ko.style.display = ko.style.display === "none" ? "block" : "none";
};

window.loadCategory = (cat, btn) => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    renderCards(categoryData[cat] || []);
};

// 앱 시작
init();
