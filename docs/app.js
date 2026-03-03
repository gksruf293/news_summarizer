import { pipeline } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.6.0';

let categoryData = {};
let embeddingData = [];
let extractor = null;
let currentSelectedArticle = null;

async function init() {
    try {
        const [catRes, embRes] = await Promise.all([
            fetch('data/category.json'),
            fetch('data/embedding.json')
        ]);
        categoryData = await catRes.json();
        embeddingData = await embRes.json();

        // 브라우저용 실시간 임베딩 모델 로드
        extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        console.log("AI Model Loaded");
        
        loadCategory('general', document.querySelector('.tab-btn.active'));
    } catch (err) {
        console.error("데이터 로드 실패:", err);
    }
}

// AI 임베딩 검색 (HuggingFace와 연동)
window.handleSearch = async function() {
    const query = document.getElementById("interestInput").value;
    if(!query || !extractor) return;

    const output = await extractor(query, { pooling: 'mean', normalize: true });
    const userVector = Array.from(output.data);

    // 코사인 유사도 계산 및 정렬
    const scored = embeddingData.map(art => ({
        ...art,
        score: cosineSimilarity(userVector, art.embedding)
    })).sort((a, b) => b.score - a.score);

    renderCards(scored.slice(0, 10));
};

function cosineSimilarity(a, b) {
    let dot = 0, nA = 0, nB = 0;
    for (let i = 0; i < a.length; i++) {
        dot += a[i] * b[i];
        nA += a[i] * a[i];
        nB += b[i] * b[i];
    }
    return dot / (Math.sqrt(nA) * Math.sqrt(nB));
}

// UI 렌더링 함수
function renderCards(articles) {
    const container = document.getElementById("results-container");
    container.innerHTML = "";
    articles.forEach(art => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
            <img src="${art.image || 'https://via.placeholder.com/300x180'}" alt="news">
            <div class="card-info">
                <h3>${art.title}</h3>
                <p>${art.description || (art.summaries ? art.summaries.elementary.slice(0, 80) : '')}...</p>
            </div>
        `;
        card.onclick = () => openModal(art);
        container.appendChild(card);
    });
}

// 모달 다층 요약 제어
window.updateSummaryLevel = function(level) {
    if(!currentSelectedArticle) return;
    document.getElementById("summary-text").innerText = currentSelectedArticle.summaries[level];
    
    document.querySelectorAll(".level-btn").forEach(btn => btn.classList.remove("active"));
    document.getElementById(`btn-${level}`).classList.add("active");
};

window.openModal = function(article) {
    currentSelectedArticle = article;
    document.getElementById("modal-title").innerText = article.title;
    document.getElementById("modal-link").href = article.url;
    document.getElementById("modal").style.display = "block";
    updateSummaryLevel('elementary'); // 기본값
};

window.closeModal = () => document.getElementById("modal").style.display = "none";

window.loadCategory = (cat, btn) => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    renderCards(categoryData[cat] || []);
};

init();

// 날짜 선택 이벤트 리스너 추가
document.getElementById('datePicker').addEventListener('change', (e) => {
    loadDataByDate(e.target.value);
});

async function loadDataByDate(date) {
    const container = document.getElementById("results-container");
    container.innerHTML = `<p>${date} 데이터를 불러오는 중...</p>`;

    try {
        // 날짜별 폴더(docs/data/YYYY-MM-DD/...)에서 파일 가져오기
        const [catRes, embRes] = await Promise.all([
            fetch(`data/${date}/category.json`),
            fetch(`data/${date}/embedding.json`)
        ]);

        if (!catRes.ok || !embRes.ok) throw new Error("해당 날짜의 데이터가 없습니다.");

        categoryData = await catRes.json();
        embeddingData = await embRes.json();

        // 현재 선택된 카테고리 탭에 맞춰 다시 렌더링
        const activeTab = document.querySelector('.tab-btn.active').innerText.toLowerCase();
        renderCards(categoryData[activeTab] || []);
        
    } catch (err) {
        container.innerHTML = `<p class="error-msg">${date}에 생성된 뉴스 데이터가 아직 없습니다.</p>`;
    }
}
