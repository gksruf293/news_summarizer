import { pipeline } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.6.0';

let categoryData = {};
let embeddingData = [];
let extractor = null;
let currentSelectedArticle = null;

async function init() {
    const container = document.getElementById("results-container");
    const searchBtn = document.getElementById("searchBtn");
    
    if (searchBtn) searchBtn.disabled = true;
    container.innerHTML = `<div class="status-msg">AI 언어 모델 로드 중...</div>`;

    try {
        // 1. 모델 로드 (성공 시 콘솔에 찍힘)
        extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        console.log("✅ AI Model Loaded");
        
        // 2. 데이터 로드 시작
        await loadDataByDate('latest');
        
        if (searchBtn) { 
            searchBtn.disabled = false; 
            searchBtn.innerText = "AI 시맨틱 검색"; 
        }
    } catch (err) {
        console.error("Init Error:", err);
        container.innerHTML = `<div class="error-msg">초기화 실패. 새로고침 해주세요.</div>`;
    }
}

window.loadDataByDate = async function(date) {
    const container = document.getElementById("results-container");
    try {
        // 캐시 방지를 위해 쿼리 스트링 추가 (매번 새 데이터를 가져오도록)
        const cacheBust = `?t=${new Date().getTime()}`;
        
        // 경로 앞에 ./ 를 붙여 상대 경로를 명확히 합니다.
        const [catRes, embRes] = await Promise.all([
            fetch(`./docs/data/${date}/category.json${cacheBust}`),
            fetch(`./docs/data/${date}/embedding.json${cacheBust}`)
        ]);

        if (!catRes.ok || !embRes.ok) throw new Error("데이터 파일을 찾을 수 없습니다.");
        
        categoryData = await catRes.json();
        const embJson = await embRes.json();
        
        // 데이터가 배열인지 엄격히 체크
        embeddingData = Array.isArray(embJson) ? embJson : [];
        
        console.log(`📊 데이터 로드 완료 | 카테고리: ${Object.keys(categoryData).length} | 임베딩: ${embeddingData.length}`);

        if (embeddingData.length === 0) {
            console.warn("⚠️ 경고: embedding.json이 비어있거나 형식이 잘못되었습니다.");
        }

        // 기본 화면 렌더링 (general 카테고리 우선)
        const defaultCat = categoryData['general'] ? 'general' : Object.keys(categoryData)[0];
        renderCards(categoryData[defaultCat] || []);

    } catch (err) {
        console.error("Data Load Error:", err);
        container.innerHTML = `<div class="error-msg">데이터 로드 실패: ${err.message}</div>`;
    }
};

// 시맨틱 검색 함수 (기존 로직 유지하되 안전장치 추가)
window.handleSearch = async function() {
    const input = document.getElementById("interestInput");
    const query = input.value.trim();
    
    if (!query) return;
    if (!extractor || embeddingData.length === 0) {
        alert("데이터가 아직 로드되지 않았습니다. 잠시만 기다려주세요.");
        return;
    }

    const container = document.getElementById("results-container");
    container.innerHTML = `<div class="status-msg">'${query}' 관련 뉴스 분석 중...</div>`;

    try {
        const output = await extractor(query, { pooling: 'mean', normalize: true });
        const userVector = Array.from(output.data);

        const scored = embeddingData.map(art => ({
            ...art,
            score: cosineSimilarity(userVector, art.embedding)
        })).sort((a, b) => b.score - a.score);

        renderCards(scored.slice(0, 10));
    } catch (err) {
        console.error("Search Error:", err);
        container.innerHTML = `<div class="error-msg">검색 중 오류가 발생했습니다.</div>`;
    }
};

// 코사인 유사도 계산
function cosineSimilarity(a, b) {
    let dot = 0, nA = 0, nB = 0;
    for (let i = 0; i < a.length; i++) {
        dot += a[i] * b[i];
        nA += a[i] * a[i];
        nB += b[i] * b[i];
    }
    return dot / (Math.sqrt(nA) * Math.sqrt(nB));
}

// 뉴스 카드 렌더링
function renderCards(articles) {
    const container = document.getElementById("results-container");
    container.innerHTML = "";
    
    if (!articles || articles.length === 0) {
        container.innerHTML = `<div class="status-msg">표시할 뉴스가 없습니다.</div>`;
        return;
    }

    articles.forEach(art => {
        const card = document.createElement("div");
        card.className = "card";
        const scoreTag = art.score ? `<span class="score-tag">${Math.round(art.score * 100)}% 관련됨</span>` : '';
        // 요약 데이터가 없을 경우를 대비한 방어 코드
        const preview = art.summaries?.elementary?.en || art.title;
        
        card.innerHTML = `
            ${art.image ? `<img src="${art.image}" onerror="this.style.display='none'">` : ''}
            <div class="card-info">
                ${scoreTag}
                <h3>${art.title}</h3>
                <p>${preview.slice(0, 100)}...</p>
            </div>
        `;
        card.onclick = () => openModal(art);
        container.appendChild(card);
    });
}

// 모달 및 요약 제어 (기존 로직 유지)
window.openModal = (article) => {
    currentSelectedArticle = article;
    document.getElementById("modal-title").innerText = article.title;
    document.getElementById("modal-link").href = article.url;
    document.getElementById("modal").style.display = "block";
    updateSummaryLevel('elementary');
};

window.updateSummaryLevel = (level) => {
    const data = currentSelectedArticle.summaries[level];
    document.getElementById("summary-text").innerHTML = `
        <div class="english-box" onclick="toggleTranslation()">
            <p class="en-text">${data.en}</p>
            <p class="ko-text" id="ko-translation" style="display:none;">🔍 ${data.ko}</p>
            <small style="color: #3b82f6; display:block; margin-top:10px;">💡 문장을 클릭하면 한국어 해석이 나타납니다.</small>
        </div>
    `;
    document.querySelectorAll(".level-btn").forEach(btn => btn.classList.remove("active"));
    document.getElementById(`btn-${level}`).classList.add("active");
};

window.toggleTranslation = () => {
    const ko = document.getElementById("ko-translation");
    if (ko) ko.style.display = ko.style.display === "none" ? "block" : "none";
};

window.closeModal = () => document.getElementById("modal").style.display = "none";

window.loadCategory = (cat, btn) => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    renderCards(categoryData[cat] || []);
};

// 초기화 실행
init();
