import { pipeline } from 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.6.0';

let categoryData = {};
let embeddingData = [];
let extractor = null;
let currentSelectedArticle = null;

/**
 * 초기화: 모델 로드 및 날짜 변경 이벤트 바인딩
 */
async function init() {
    const container = document.getElementById("results-container");
    const searchBtn = document.getElementById("searchBtn");
    const datePicker = document.getElementById("datePicker"); // HTML의 id="datePicker"와 일치해야 함
    
    if (searchBtn) searchBtn.disabled = true;
    container.innerHTML = `<div class="status-msg">AI 모델 로딩 중...</div>`;

    try {
        extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        console.log("✅ AI Model Loaded");

        // 1. 초기 데이터 로드
        await loadDataByDate('latest');

        // 2. [중요] 날짜 변경 이벤트 리스너를 여기서 확실히 등록합니다.
        if (datePicker) {
            datePicker.addEventListener('change', (e) => {
                const selectedDate = e.target.value; 
                if (selectedDate) {
                    console.log("📅 날짜 변경 호출:", selectedDate);
                    loadDataByDate(selectedDate);
                }
            });
        }

        if (searchBtn) { 
            searchBtn.disabled = false; 
            searchBtn.innerText = "AI 시맨틱 검색"; 
        }
    } catch (err) {
        console.error("Init Error:", err);
        container.innerHTML = `<div class="error-msg">초기화 실패.</div>`;
    }
}

/**
 * 데이터 로드 함수 (window 객체에 등록하여 외부 접근 허용)
 */
window.loadDataByDate = async function(date) {
    const container = document.getElementById("results-container");
    try {
        const cacheBust = `?t=${new Date().getTime()}`;
        // 경로 앞에 ./ 를 붙여 상대 경로를 명확히 합니다.
        const [catRes, embRes] = await Promise.all([
            fetch(`./data/${date}/category.json${cacheBust}`),
            fetch(`./data/${date}/embedding.json${cacheBust}`)
        ]);

        if (!catRes.ok) throw new Error(`${date} 데이터를 찾을 수 없습니다.`);

        categoryData = await catRes.json();
        const embJson = await embRes.json();
        embeddingData = Array.isArray(embJson) ? embJson : [];
        
        console.log(`📊 ${date} 로드 완료 | 임베딩: ${embeddingData.length}개`);

        // 화면 탭 초기화 (general)
        const firstCat = categoryData['general'] ? 'general' : Object.keys(categoryData)[0];
        renderCards(categoryData[firstCat] || []);

    } catch (err) {
        console.error("Data Load Error:", err);
        container.innerHTML = `<div class="error-msg">⚠️ ${err.message}</div>`;
    }
};

/**
 * 레벨별 요약 변환 (버튼 클릭 시 호출됨)
 */
window.updateSummaryLevel = function(level) {
    // 1. 선택된 기사가 있는지 확인
    if (!currentSelectedArticle || !currentSelectedArticle.summaries) {
        console.error("선택된 기사 데이터가 없습니다.");
        return;
    }

    // 2. 해당 레벨의 데이터 가져오기 (elementary, middle, high)
    const data = currentSelectedArticle.summaries[level];
    if (!data) {
        console.error(`${level} 요약 데이터가 없습니다.`);
        return;
    }

    // 3. 모달 내부의 텍스트 영역 교체
    const summaryBox = document.getElementById("summary-text");
    if (summaryBox) {
        summaryBox.innerHTML = `
            <div class="english-box" onclick="toggleTranslation()">
                <p class="en-text">${data.en}</p>
                <p class="ko-text" id="ko-translation" style="display:none;">🔍 ${data.ko}</p>
                <small style="color: #3b82f6; display:block; margin-top:10px; cursor:pointer;">
                    💡 문장을 클릭하면 한국어 해석이 나타납니다.
                </small>
            </div>
        `;
    }

    // 4. 버튼 활성화 시각적 표시
    document.querySelectorAll(".level-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.getElementById(`btn-${level}`);
    if (activeBtn) activeBtn.classList.add("active");
};

/**
 * 뉴스 카드 렌더링
 */
function renderCards(articles) {
    const container = document.getElementById("results-container");
    container.innerHTML = "";
    
    articles.forEach(art => {
        const card = document.createElement("div");
        card.className = "card";
        const preview = art.summaries?.elementary?.en || art.title;
        
        card.innerHTML = `
            ${art.image ? `<img src="${art.image}" onerror="this.style.display='none'">` : ''}
            <div class="card-info">
                <h3>${art.title}</h3>
                <p>${preview.slice(0, 100)}...</p>
            </div>
        `;
        // 카드 클릭 시 모달 열기
        card.onclick = () => openModal(art);
        container.appendChild(card);
    });
}

window.openModal = (article) => {
    currentSelectedArticle = article;
    document.getElementById("modal-title").innerText = article.title;
    document.getElementById("modal-link").href = article.url;
    document.getElementById("modal").style.display = "block";
    // 기본적으로 초등 레벨 먼저 보여줌
    window.updateSummaryLevel('elementary');
};

// 나머지 유틸리티 함수
window.closeModal = () => document.getElementById("modal").style.display = "none";
window.toggleTranslation = () => {
    const ko = document.getElementById("ko-translation");
    if (ko) ko.style.display = ko.style.display === "none" ? "block" : "none";
};
window.loadCategory = (cat, btn) => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    renderCards(categoryData[cat] || []);
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

// 초기화 실행
init();
