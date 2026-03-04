import { pipeline } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.6.0';

let categoryData = {};
let embeddingData = [];
let extractor = null;
let currentSelectedArticle = null;

async function init() {
    const container = document.getElementById("results-container");
    const searchBtn = document.getElementById("searchBtn");
    
    if (searchBtn) searchBtn.disabled = true;
    container.innerHTML = `<div class="status-msg">AI 모델 및 데이터 로드 중...</div>`;

    try {
        // 1. 모델 로드
        extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        console.log("✅ AI Model Loaded");

        // 2. 데이터 로드 (가장 최신 데이터 우선 시도)
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
        // GitHub Pages 환경에서는 경로 앞에 ./ 를 붙이는 것이 가장 안전합니다.
        // 캐시 방지를 위해 쿼리 스트링 추가
        const cacheBust = `?t=${new Date().getTime()}`;
        const basePath = `./data/${date}`;

        const [catRes, embRes] = await Promise.all([
            fetch(`${basePath}/category.json${cacheBust}`),
            fetch(`${basePath}/embedding.json${cacheBust}`)
        ]);

        if (!catRes.ok || !embRes.ok) {
            throw new Error(`파일을 찾을 수 없습니다. (Status: ${catRes.status})`);
        }

        categoryData = await catRes.json();
        const embJson = await embRes.json();
        
        // 데이터 할당 및 검증
        embeddingData = Array.isArray(embJson) ? embJson : [];
        
        console.log(`📊 데이터 로드 완료 | 경로: ${basePath} | 임베딩 개수: ${embeddingData.length}`);

        if (embeddingData.length > 0) {
            const defaultCat = categoryData['general'] ? 'general' : Object.keys(categoryData)[0];
            renderCards(categoryData[defaultCat] || []);
        } else {
            console.warn("⚠️ embedding.json 파일은 읽었으나 내용이 비어있습니다.");
            container.innerHTML = `<div class="error-msg">검색 가능한 데이터가 없습니다. (0개)</div>`;
        }

    } catch (err) {
        console.error("Data Load Error:", err);
        // 'latest' 로딩 실패 시, 오늘 날짜로 재시도하는 로직 (보험)
        const today = new Date().toISOString().split('T')[0];
        if (date === 'latest') {
            console.log(`Re-trying with today's date: ${today}`);
            return await loadDataByDate(today);
        }
        container.innerHTML = `<div class="error-msg">데이터 로드 실패: ${err.message}</div>`;
    }
};

// ... (renderCards, handleSearch, cosineSimilarity 등 나머지 함수는 기존과 동일하게 유지)

function renderCards(articles) {
    const container = document.getElementById("results-container");
    container.innerHTML = "";
    
    if (!articles || articles.length === 0) {
        container.innerHTML = `<div class="status-msg">뉴스가 없습니다.</div>`;
        return;
    }

    articles.forEach(art => {
        const card = document.createElement("div");
        card.className = "card";
        const scoreTag = art.score ? `<span class="score-tag">${Math.round(art.score * 100)}% 관련됨</span>` : '';
        const preview = art.summaries?.elementary?.en || art.title || "No content";
        
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

// 초기화 실행
init();

