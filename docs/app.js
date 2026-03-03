/* 요약 수준 변경 시 시각화 업데이트 */
function updateSummaryLevel(level) {
    const article = window.selectedArticle;
    const textBox = document.getElementById("modal-text");
    
    // 저장된 다층 요약 데이터에서 선택한 레벨 가져오기
    textBox.innerText = article.summaries[level];
    
    // 버튼 스타일 업데이트
    document.querySelectorAll('.level-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`btn-${level}`).classList.add('active');
}

/* 모달 열기 */
function openModal(article) {
    window.selectedArticle = article;
    document.getElementById("modal-title").innerText = article.title;
    document.getElementById("modal").style.display = "block";
    
    // 기본값으로 초등 요약 표시
    updateSummaryLevel('elementary');
}
