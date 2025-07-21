// 앱 상태 관리
const AppState = {
    selectedMode: 'quick',
    currentChart: null,
    currentHtmlReport: null,
    currentQuestion: null
};

// 앱 초기화
function initApp() {
    UI.renderInfoBox();
    UI.renderQuerySection();
    UI.renderExamplesSection();
    setupEventListeners();
    
    console.log('🚀 GA4 자연어 분석 시스템이 시작되었습니다.');
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 질문 실행
    document.getElementById('executeBtn').addEventListener('click', executeQuery);
    
    // 키보드 단축키
    document.addEventListener('keydown', handleKeyboard);
    
    // 질문 입력창 이벤트
    const questionInput = document.getElementById('question');
    questionInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            executeQuery();
        }
    });
    
    // 포커스 시 랜덤 placeholder
    questionInput.addEventListener('focus', () => {
        if (!questionInput.value) {
            const randomExample = Examples.getRandomQuestion();
            questionInput.placeholder = `예: ${randomExample}`;
        }
    });
}

// 키보드 이벤트 처리
function handleKeyboard(e) {
    // Alt + 1,2,3으로 모드 전환
    if (e.altKey) {
        const modes = ['quick', 'structured', 'creative'];
        const modeIndex = parseInt(e.key) - 1;
        if (modeIndex >= 0 && modeIndex < modes.length) {
            selectMode(modes[modeIndex]);
        }
    }
    
    // Esc로 로딩 취소
    if (e.key === 'Escape') {
        UI.setLoading(false);
    }
}

// 모드 선택
function selectMode(mode) {
    AppState.selectedMode = mode;
    UI.updateModeSelection(mode);
    UI.updateExecuteButton(mode);
}

// 질문 설정
function setQuestion(question) {
    const questionInput = document.getElementById('question');
    questionInput.value = question;
    questionInput.focus();
    UI.highlightInput(questionInput);
}

// 쿼리 실행
async function executeQuery() {
    const question = document.getElementById('question').value.trim();
    
    if (!question) {
        UI.showMessage('질문을 입력해주세요.', 'error');
        document.getElementById('question').focus();
        return;
    }

    UI.setLoading(true, AppState.selectedMode);

    try {
        const data = await API.executeQuery(question, AppState.selectedMode);
        displayResults(data);
        UI.showMessage('분석이 완료되었습니다!', 'success');
    } catch (error) {
        console.error('Error:', error);
        UI.showMessage(`오류: ${error.message}`, 'error');
    } finally {
        UI.setLoading(false);
    }
}

// 결과 표시
function displayResults(data) {
    UI.showResults();
    UI.updateResultsHeader(data);
    
    if (data.mode === 'creative') {
        UI.showCreativeResults(data);
        AppState.currentHtmlReport = data.html_content;
        AppState.currentQuestion = data.original_question;
    } else {
        UI.showDataResults(data);
        UI.showQueryResults(data);
        if (data.mode === 'structured') {
            UI.showAnalysisResults(data);
            if (data.chart_config) {
                setTimeout(() => {
                    AppState.currentChart = ChartManager.createChart(data.data, data.chart_config);
                }, 100);
            }
        }
    }
    
    UI.scrollToResults();
}

// HTML 리포트 함수들
function openInNewWindow() {
    if (AppState.currentHtmlReport) {
        const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes');
        newWindow.document.write(AppState.currentHtmlReport);
        newWindow.document.close();
    }
}

function downloadHtml() {
    if (AppState.currentHtmlReport) {
        Utils.downloadFile(AppState.currentHtmlReport, 'text/html', 'ga4-analysis.html');
        UI.showMessage('파일이 다운로드되었습니다.', 'success');
    }
}

function regenerateHtml() {
    selectMode('creative');
    executeQuery();
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', initApp);