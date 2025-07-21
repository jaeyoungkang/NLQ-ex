// static/js/main.js
// 메인 애플리케이션 로직 및 공통 유틸리티 함수

// 전역 변수
const questionInput = document.getElementById('questionInput');
const quickBtn = document.getElementById('quickBtn');
const structuredBtn = document.getElementById('structuredBtn');
const creativeBtn = document.getElementById('creativeBtn');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const resultsSection = document.getElementById('resultsSection');

let selectedMode = 'structured';

// 모드 선택 카드 이벤트
document.querySelectorAll('.mode-card').forEach(card => {
    card.addEventListener('click', function() {
        // 기존 선택 제거
        document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('selected'));
        // 새 선택 추가
        this.classList.add('selected');
        selectedMode = this.dataset.mode;
    });
});

// 예시 질문 설정 함수
function setQuestion(question) {
    questionInput.value = question;
    questionInput.focus();
}

// Enter 키로 질문 전송 (Ctrl+Enter)
questionInput.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        executeQuery(selectedMode);
    }
});

// 버튼 이벤트들
quickBtn.addEventListener('click', () => executeQuery('quick'));
structuredBtn.addEventListener('click', () => executeQuery('structured'));
creativeBtn.addEventListener('click', () => executeQuery('creative'));

// 질문 실행 함수
async function executeQuery(mode) {
    const question = questionInput.value.trim();

    if (!question) {
        alert('질문을 입력해주세요.');
        questionInput.focus();
        return;
    }

    // UI 상태 변경
    setLoadingState(true, mode);

    try {
        // 모드별 엔드포인트 결정
        const endpoints = {
            'quick': '/quick',
            'structured': '/analyze',
            'creative': '/creative-html'
        };

        const response = await fetch(endpoints[mode], {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            displayResults(data, mode);
        } else {
            displayError(data.error || '알 수 없는 오류가 발생했습니다.', mode);
        }
    } catch (error) {
        console.error('API 호출 오류:', error);
        displayError(`네트워크 오류: ${error.message}`, mode);
    } finally {
        setLoadingState(false);
    }
}

// 로딩 상태 설정
function setLoadingState(isLoading, mode = '') {
    quickBtn.disabled = isLoading;
    structuredBtn.disabled = isLoading;
    creativeBtn.disabled = isLoading;
    loading.style.display = isLoading ? 'flex' : 'none';
    
    if (isLoading) {
        const messages = {
            'quick': '빠르게 데이터를 조회하고 있습니다...',
            'structured': 'AI가 데이터를 분석하고 차트를 생성하고 있습니다...',
            'creative': 'Claude가 창의적인 HTML 리포트를 생성하고 있습니다... (30초 소요)'
        };
        loadingText.textContent = messages[mode] || '데이터를 처리하고 있습니다...';
        
        const btnTexts = {
            'quick': '⏳ 조회 중...',
            'structured': '⏳ 분석 중...',
            'creative': '⏳ 생성 중...'
        };
        quickBtn.innerHTML = btnTexts['quick'];
        structuredBtn.innerHTML = btnTexts['structured'];
        creativeBtn.innerHTML = btnTexts['creative'];
    } else {
        quickBtn.innerHTML = '⚡ 빠른 조회<div class="btn-description">데이터만 빠르게</div>';
        structuredBtn.innerHTML = '📊 구조화 분석<div class="btn-description">차트 + 리포트</div>';
        creativeBtn.innerHTML = '🎨 창의적 HTML<div class="btn-description">독립 문서 생성</div>';
    }
}

// 결과 표시 (모드별 분기)
function displayResults(data, mode) {
    if (mode === 'creative') {
        displayCreativeHtmlResults(data);
    } else if (mode === 'structured') {
        displayStructuredResults(data);
    } else {
        displayQuickResults(data);
    }
}

// 빠른 조회 결과 표시
function displayQuickResults(data) {
    const resultHtml = `
        <div class="results-header">
            <h2>⚡ 빠른 조회 결과 <span class="mode-badge quick">QUICK</span></h2>
            <div class="result-count">${data.row_count}개 결과</div>
        </div>

        <div class="query-info">
            <h3>📝 쿼리 정보</h3>
            <div class="original-question">
                <strong>원본 질문:</strong> ${escapeHtml(data.original_question)}
            </div>
            <div class="generated-sql">
                <strong>생성된 SQL:</strong><br>
                ${escapeHtml(data.generated_sql)}
            </div>
        </div>

        <div class="table-container">
            ${createTable(data.data)}
        </div>

        <div class="success">
            <h3>✅ 조회 완료</h3>
            <p>총 ${data.row_count}개의 결과를 빠르게 조회했습니다.</p>
            <p>💡 더 자세한 분석을 원하시면 "구조화 분석" 모드를 사용해보세요.</p>
        </div>
    `;

    resultsSection.innerHTML = resultHtml;
}

// 창의적 HTML 결과 표시
function displayCreativeHtmlResults(data) {
    const qualityBadge = data.quality_score >= 80 ? 
        `<span style="background: #34a853; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">고품질</span>` :
        data.quality_score >= 60 ?
        `<span style="background: #ffa726; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">양호</span>` :
        `<span style="background: #ff6b6b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">기본</span>`;

    const resultHtml = `
        <div class="results-header">
            <h2>🎨 창의적 HTML 리포트 <span class="mode-badge creative">CREATIVE</span></h2>
            <div class="result-count">${data.row_count}개 결과 • ${qualityBadge}</div>
        </div>
        
        <div class="html-controls">
            <button onclick="openInNewWindow()" class="btn btn-structured">🔗 새 창에서 열기</button>
            <button onclick="downloadHtml()" class="btn btn-quick">💾 HTML 다운로드</button>
            ${data.is_fallback ? '<button onclick="regenerateHtml()" class="btn btn-creative">🔄 재생성</button>' : ''}
        </div>
        
        ${data.is_fallback ? `
        <div class="html-warning">
            ⚠️ <strong>알림:</strong> 고급 HTML 생성에 실패하여 기본 형태로 표시됩니다. 재생성을 시도해보세요.
        </div>
        ` : ''}
        
        <div class="iframe-container">
            <iframe 
                id="htmlReportFrame"
                style="width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 8px;"
                sandbox="allow-scripts allow-same-origin">
            </iframe>
        </div>
        
        <div class="success">
            <h3>✅ HTML 리포트 생성 완료</h3>
            <p>Claude가 ${data.attempts}번의 시도를 통해 독립적인 HTML 리포트를 생성했습니다.</p>
            <p>품질 점수: ${data.quality_score}/100 | 총 ${data.row_count}개 결과 분석</p>
        </div>
    `;
    
    resultsSection.innerHTML = resultHtml;
    
    // iframe에 HTML 내용 로드
    const iframe = document.getElementById('htmlReportFrame');
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    doc.open();
    doc.write(data.html_content);
    doc.close();
    
    // 전역 변수에 HTML 저장
    window.currentHtmlReport = data.html_content;
    window.currentQuestion = data.original_question;
}

// 유틸리티 함수들

// 새 창에서 열기
function openInNewWindow() {
    if (window.currentHtmlReport) {
        const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes');
        newWindow.document.write(window.currentHtmlReport);
        newWindow.document.close();
    }
}

// HTML 다운로드
function downloadHtml() {
    if (window.currentHtmlReport) {
        const blob = new Blob([window.currentHtmlReport], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ga4-analysis-${window.currentQuestion?.replace(/[^a-zA-Z0-9]/g, '-') || 'report'}-${new Date().toISOString().slice(0,10)}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// HTML 재생성
function regenerateHtml() {
    executeQuery('creative');
}

// 테이블 생성
function createTable(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">조회된 데이터가 없습니다.</div>';
    }

    // 헤더 생성
    const headers = Object.keys(data[0]);
    const headerHtml = headers.map(header => 
        `<th>${escapeHtml(header)}</th>`
    ).join('');

    // 행 생성
    const rowsHtml = data.map(row => {
        const cellsHtml = headers.map(header => {
            const value = row[header];
            return `<td>${formatCellValue(value)}</td>`;
        }).join('');
        return `<tr>${cellsHtml}</tr>`;
    }).join('');

    return `
        <table>
            <thead>
                <tr>${headerHtml}</tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
    `;
}

// 셀 값 포맷팅
function formatCellValue(value) {
    if (value === null || value === undefined) {
        return '<em style="color: #999;">NULL</em>';
    }
    
    if (typeof value === 'number') {
        // 숫자는 천 단위 구분자 추가
        return value.toLocaleString();
    }
    
    if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
        // 날짜 형식 감지 및 포맷팅
        try {
            const date = new Date(value);
            return date.toLocaleDateString('ko-KR');
        } catch (e) {
            return escapeHtml(value);
        }
    }
    
    return escapeHtml(String(value));
}

// 오류 표시
function displayError(errorMessage, mode) {
    const modeLabels = {
        'quick': '빠른 조회',
        'structured': '구조화 분석',
        'creative': '창의적 HTML'
    };

    const errorHtml = `
        <div class="error">
            <h3>❌ ${modeLabels[mode]} 오류 발생</h3>
            <p>${escapeHtml(errorMessage)}</p>
            <p><small>서버 로그를 확인하거나 다른 질문을 시도해보세요.</small></p>
        </div>
    `;

    resultsSection.innerHTML = errorHtml;
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 예시 질문 자동 완성
const exampleQuestions = [
    "오늘 총 이벤트 수를 알려주세요",
    "가장 인기 있는 이벤트 유형을 보여주세요",
    "국가별 사용자 분포를 보여주세요",
    "모바일 사용자 비율을 알려주세요",
    "시간대별 활동량을 보여주세요",
    "구매 관련 이벤트를 분석해주세요",
    "트래픽 소스별 성과를 보여주세요",
    "운영체제별 사용자 현황을 알려주세요"
];

// 질문 입력창 포커스 시 예시 표시
questionInput.addEventListener('focus', function() {
    if (!this.value) {
        this.placeholder = exampleQuestions[Math.floor(Math.random() * exampleQuestions.length)];
    }
});

// 페이지 로드 시 질문 입력창에 포커스
window.addEventListener('load', function() {
    questionInput.focus();
});