// static/js/main.js
// 개선된 메인 애플리케이션 로직 - 단계별 UX 및 실시간 모니터링 지원

// 전역 변수
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const charCount = document.getElementById('charCount');
const conversationHistory = document.getElementById('conversationHistory');

let currentStepId = 0;
let lastQuickQueryData = null;
let isProcessing = false;

// 예시 질문 설정 함수
function setQuestion(question) {
    questionInput.value = question;
    questionInput.focus();
    updateCharCount();
}

// 문자 수 카운트 업데이트
function updateCharCount() {
    const count = questionInput.value.length;
    charCount.textContent = `${count}/500`;
    if (count > 500) {
        charCount.style.color = '#ef4444';
    } else {
        charCount.style.color = '#6b7280';
    }
}

// Enter 키 처리 (Shift+Enter는 줄바꿈, Enter는 전송)
questionInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!isProcessing && this.value.trim()) {
            sendMessage();
        }
    }
});

// 입력 시 문자 수 업데이트
questionInput.addEventListener('input', updateCharCount);

// 전송 버튼 클릭
sendBtn.addEventListener('click', () => {
    if (!isProcessing && questionInput.value.trim()) {
        sendMessage();
    }
});

// 메시지 전송 함수
async function sendMessage() {
    const question = questionInput.value.trim();
    
    if (!question || question.length > 500) {
        return;
    }
    
    isProcessing = true;
    updateUIState(true);
    
    // 1. 사용자 메시지 표시
    showUserMessage(question);
    
    // 2. 입력창 초기화
    questionInput.value = '';
    updateCharCount();
    
    try {
        // 3. LLM에게 분석 유형 판단 요청
        const analysisDecision = await requestAnalysisDecision(question);
        
        if (analysisDecision.needsAnalysis) {
            // 4. 분석이 필요한 경우 - 사용자에게 분석 옵션 제시
            await showAnalysisOptions(question, analysisDecision.analysisTypes);
        } else {
            // 5. 단순 조회만 필요한 경우 - 바로 실행
            await executeSimpleQuery(question);
        }
        
    } catch (error) {
        showErrorMessage(`처리 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        isProcessing = false;
        updateUIState(false);
    }
}

// UI 상태 업데이트
function updateUIState(processing) {
    sendBtn.disabled = processing;
    questionInput.disabled = processing;
    
    if (processing) {
        sendBtn.innerHTML = `
            <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
        `;
    } else {
        sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    }
}

// 사용자 메시지 표시
function showUserMessage(message) {
    const userMessageHtml = `
        <div class="flex justify-end mb-4">
            <div class="bg-google-blue text-white p-4 rounded-lg max-w-[80%] break-words">
                <div class="font-medium mb-1">👤 사용자</div>
                <div>${escapeHtml(message)}</div>
            </div>
        </div>
    `;
    conversationHistory.insertAdjacentHTML('beforeend', userMessageHtml);
    scrollToBottom();
}

// AI 응답 표시 (스트리밍 스타일)
function showAIMessage(message, type = 'assistant') {
    const iconMap = {
        'assistant': '🤖',
        'system': '⚙️',
        'analysis': '📊'
    };
    
    const bgColorMap = {
        'assistant': 'bg-gray-100',
        'system': 'bg-blue-50',
        'analysis': 'bg-green-50'
    };
    
    const messageId = `ai-message-${Date.now()}`;
    const aiMessageHtml = `
        <div class="flex justify-start mb-4">
            <div class="${bgColorMap[type]} p-4 rounded-lg max-w-[80%] break-words" id="${messageId}">
                <div class="font-medium mb-2">${iconMap[type]} AI 어시스턴트</div>
                <div class="ai-content">${message}</div>
            </div>
        </div>
    `;
    conversationHistory.insertAdjacentHTML('beforeend', aiMessageHtml);
    scrollToBottom();
    return messageId;
}

// 페이지 하단으로 스크롤
function scrollToBottom() {
    setTimeout(() => {
        conversationHistory.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'end' 
        });
    }, 100);
}

// LLM에게 분석 유형 판단 요청
async function requestAnalysisDecision(question) {
    showAIMessage("질문을 분석하고 있습니다...", 'system');
    
    // 실제로는 백엔드 API 호출
    // 임시로 간단한 키워드 기반 판단 로직
    const analysisKeywords = ['분석', '비교', '트렌드', '패턴', '인사이트', '리포트', '차트', '시각화'];
    const needsAnalysis = analysisKeywords.some(keyword => question.includes(keyword));
    
    await sleep(1000); // 실제 API 호출 시뮬레이션
    
    if (needsAnalysis) {
        return {
            needsAnalysis: true,
            analysisTypes: ['구조화 분석', '창의적 HTML 리포트']
        };
    } else {
        return {
            needsAnalysis: false
        };
    }
}

// 분석 옵션 제시
async function showAnalysisOptions(question, analysisTypes) {
    const optionsHtml = `
        질문을 분석한 결과, 더 깊이 있는 분석이 도움이 될 것 같습니다.<br><br>
        어떤 방식으로 분석을 진행할까요?<br><br>
        <div class="flex flex-wrap gap-2 mt-3">
            <button onclick="executeAnalysis('${escapeHtml(question)}', 'quick')" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                📊 기본 조회만
            </button>
            <button onclick="executeAnalysis('${escapeHtml(question)}', 'structured')" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                📈 구조화 분석
            </button>
            <button onclick="executeAnalysis('${escapeHtml(question)}', 'creative')" class="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                🎨 창의적 HTML 리포트
            </button>
        </div>
    `;
    
    showAIMessage(optionsHtml, 'analysis');
}

// 분석 실행 (전역 함수로 만들어 onclick에서 호출 가능)
window.executeAnalysis = async function(question, analysisType) {
    // 선택 버튼들 비활성화
    const buttons = document.querySelectorAll('#conversationHistory button');
    buttons.forEach(btn => btn.disabled = true);
    
    isProcessing = true;
    updateUIState(true);
    
    try {
        if (analysisType === 'quick') {
            await executeSimpleQuery(question);
        } else if (analysisType === 'structured') {
            await executeStructuredAnalysis(question);
        } else if (analysisType === 'creative') {
            await executeCreativeAnalysis(question);
        }
    } catch (error) {
        showErrorMessage(`분석 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        isProcessing = false;
        updateUIState(false);
    }
};

// 단순 조회 실행
async function executeSimpleQuery(question) {
    const messageId = showAIMessage("쿼리를 생성하고 있습니다...", 'system');
    
    try {
        // SQL 생성
        const response = await fetch('/quick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // 쿼리 생성 완료 메시지 업데이트
            document.querySelector(`#${messageId} .ai-content`).innerHTML = `
                ✅ SQL 쿼리가 생성되었습니다:<br><br>
                <code class="block bg-gray-200 p-3 rounded text-sm font-mono whitespace-pre-wrap overflow-x-auto">${escapeHtml(data.generated_sql)}</code>
            `;
            
            // 데이터 조회 중 메시지
            const queryingId = showAIMessage("데이터를 조회하고 있습니다...", 'system');
            
            await sleep(500);
            
            // 결과 표시
            document.querySelector(`#${queryingId} .ai-content`).innerHTML = `
                ✅ 조회가 완료되었습니다. (총 ${data.row_count}개 결과)<br><br>
                <div class="table-container">${createTable(data.data)}</div>
            `;
            
        } else {
            document.querySelector(`#${messageId} .ai-content`).textContent = 
                `❌ 오류: ${data.error || '쿼리 생성에 실패했습니다.'}`;
        }
        
    } catch (error) {
        document.querySelector(`#${messageId} .ai-content`).textContent = 
            `❌ 네트워크 오류: ${error.message}`;
    }
}

// 구조화 분석 실행
async function executeStructuredAnalysis(question) {
    const messageId = showAIMessage("구조화 분석을 수행하고 있습니다...", 'analysis');
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            document.querySelector(`#${messageId} .ai-content`).innerHTML = `
                ✅ 구조화 분석이 완료되었습니다.<br><br>
                <div class="bg-green-50 p-4 rounded-lg mb-4">
                    <h4 class="font-semibold mb-2">📊 AI 분석 리포트</h4>
                    <div>${parseMarkdown(data.analysis_report)}</div>
                </div>
                <div class="table-container">${createTable(data.data)}</div>
            `;
        } else {
            document.querySelector(`#${messageId} .ai-content`).textContent = 
                `❌ 분석 오류: ${data.error || '구조화 분석에 실패했습니다.'}`;
        }
        
    } catch (error) {
        document.querySelector(`#${messageId} .ai-content`).textContent = 
            `❌ 네트워크 오류: ${error.message}`;
    }
}

// 창의적 HTML 분석 실행
async function executeCreativeAnalysis(question) {
    const messageId = showAIMessage("창의적 HTML 리포트를 생성하고 있습니다...", 'analysis');
    
    try {
        const response = await fetch('/creative-html', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            document.querySelector(`#${messageId} .ai-content`).innerHTML = `
                ✅ 창의적 HTML 리포트가 생성되었습니다.<br><br>
                <div class="flex gap-2 mb-4">
                    <button onclick="openHtmlInNewWindow()" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">🔗 새 창에서 열기</button>
                    <button onclick="downloadHtmlReport()" class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">💾 다운로드</button>
                </div>
                <iframe 
                    style="width: 100%; height: 400px; border: 1px solid #ddd; border-radius: 8px;"
                    sandbox="allow-scripts allow-same-origin">
                </iframe>
            `;
            
            // iframe에 HTML 로드
            const iframe = document.querySelector(`#${messageId} iframe`);
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            doc.open();
            doc.write(data.html_content);
            doc.close();
            
            // 전역 변수에 저장
            window.currentHtmlReport = data.html_content;
            window.currentQuestion = question;
            
        } else {
            document.querySelector(`#${messageId} .ai-content`).textContent = 
                `❌ 생성 오류: ${data.error || 'HTML 리포트 생성에 실패했습니다.'}`;
        }
        
    } catch (error) {
        document.querySelector(`#${messageId} .ai-content`).textContent = 
            `❌ 네트워크 오류: ${error.message}`;
    }
}

// HTML 리포트 관련 함수들
window.openHtmlInNewWindow = function() {
    if (window.currentHtmlReport) {
        const newWindow = window.open('', '_blank', 'width=1200,height=800,scrollbars=yes');
        newWindow.document.write(window.currentHtmlReport);
        newWindow.document.close();
    }
};

window.downloadHtmlReport = function() {
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
};

// 오류 메시지 표시
function showErrorMessage(message) {
    showAIMessage(`❌ ${message}`, 'system');
}

// sleep 함수
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

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

    if (mode === 'quick') {
        // 1단계: 쿼리 생성 메시지 표시
        showQueryGenerationStatus("쿼리를 생성하고 있습니다...");
        
        try {
            // SQL 생성 API 호출
            const sqlResponse = await fetch('/quick', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question, step: 'sql_only' })
            });
            
            const sqlData = await sqlResponse.json();
            
            if (sqlResponse.ok && sqlData.success && sqlData.generated_sql) {
                // 2단계: 생성된 쿼리 표시
                showGeneratedQuery(sqlData.generated_sql, question);
                
                // 3단계: 데이터 조회 메시지
                await sleep(1000);
                showDataQueryStatus("데이터를 조회하고 있습니다...");
                
                // 실제 데이터 조회
                const dataResponse = await fetch('/quick', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await dataResponse.json();
                
                if (dataResponse.ok && data.success) {
                    // 4단계: 결과 표시
                    displayQuickResults(data);
                    lastQuickQueryData = data;
                    enableAdvancedAnalysis();
                } else {
                    displayError(data.error || '데이터 조회 중 오류가 발생했습니다.', mode);
                }
            } else {
                displayError(sqlData.error || 'SQL 생성 중 오류가 발생했습니다.', mode);
            }
        } catch (error) {
            console.error('API 호출 오류:', error);
            displayError(`네트워크 오류: ${error.message}`, mode);
        }
    } else {
        // 기존 구조화/창의적 분석 로직
        try {
            const endpoints = {
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
        }
    }
    
    setLoadingState(false);
}

// sleep 함수 (UI 업데이트 지연용)
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 고급 분석 옵션 활성화
function enableAdvancedAnalysis() {
    setTimeout(() => {
        analysisOptions.classList.add('show');
        structuredBtn.disabled = false;
        creativeBtn.disabled = false;
        
        // 스크롤을 고급 분석 옵션으로 부드럽게 이동
        analysisOptions.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
    }, 500);
}

// 로딩 상태 설정
function setLoadingState(isLoading, mode = '') {
    // 빠른 조회는 항상 비활성화/활성화
    quickBtn.disabled = isLoading;
    
    // 고급 분석 버튼들은 빠른 조회가 완료된 경우에만 활성화 가능
    if (mode !== 'quick') {
        structuredBtn.disabled = isLoading;
        creativeBtn.disabled = isLoading;
    }
    
    if (isLoading) {
        if (mode === 'quick') {
            quickBtn.innerHTML = '<span class="btn-main-text">⏳ 조회 중...</span><div class="btn-description">잠시만 기다려주세요</div>';
        } else if (mode === 'structured') {
            structuredBtn.innerHTML = '<span class="btn-main-text">⏳ 분석 중...</span><div class="btn-description">AI가 분석하고 있습니다</div>';
        } else if (mode === 'creative') {
            creativeBtn.innerHTML = '<span class="btn-main-text">⏳ 생성 중...</span><div class="btn-description">HTML 리포트 생성 중</div>';
        }
    } else {
        // 원래 버튼 텍스트 복원
        quickBtn.innerHTML = `
            <span class="btn-main-text">📊 조회</span>
            <div class="btn-description">데이터를 먼저 확인해보세요</div>
        `;
        structuredBtn.innerHTML = `
            <span class="btn-main-text">📊 구조화 분석</span>
            <div class="btn-description">차트 + AI 리포트 생성</div>
        `;
        creativeBtn.innerHTML = `
            <span class="btn-main-text">🎨 창의적 HTML</span>
            <div class="btn-description">독립 문서 생성</div>
        `;
    }
}

// 결과 표시 (모드별 분기)
function displayResults(data, mode) {
    if (mode === 'quick') {
        displayQuickResults(data);
    } else if (mode === 'structured') {
        displayStructuredResults(data);
    } else if (mode === 'creative') {
        displayCreativeHtmlResults(data);
    }
}

// 새로운 UX 단계별 표시 함수들

// 1단계: 쿼리 생성 상태 표시
function showQueryGenerationStatus(message) {
    const statusHtml = `
        <div id="queryGenerationStatus" class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div class="flex items-center">
                <div class="spinner mr-3"></div>
                <div>
                    <h4 class="font-semibold text-blue-800">🔄 SQL 쿼리 생성 중</h4>
                    <p class="text-blue-600 text-sm">${message}</p>
                </div>
            </div>
        </div>
    `;
    conversationHistory.insertAdjacentHTML('beforeend', statusHtml);
}

// 2단계: 생성된 쿼리 표시
function showGeneratedQuery(sqlQuery, originalQuestion) {
    const queryHtml = `
        <div id="generatedQueryDisplay" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <h4 class="font-semibold text-green-800 mb-3">✅ SQL 쿼리 생성 완료</h4>
            <div class="bg-white p-3 rounded border border-green-200 mb-3">
                <p class="text-sm text-gray-600 mb-2"><strong>원본 질문:</strong> ${escapeHtml(originalQuestion)}</p>
                <p class="text-sm text-gray-600 mb-2"><strong>생성된 SQL:</strong></p>
                <code class="block bg-gray-100 p-3 rounded text-sm font-mono whitespace-pre-wrap overflow-x-auto">${escapeHtml(sqlQuery)}</code>
            </div>
        </div>
    `;
    document.getElementById('queryGenerationStatus').outerHTML = queryHtml;
}

// 3단계: 데이터 조회 상태 표시
function showDataQueryStatus(message) {
    const statusHtml = `
        <div id="dataQueryStatus" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div class="flex items-center">
                <div class="spinner mr-3"></div>
                <div>
                    <h4 class="font-semibold text-yellow-800">🔍 데이터 조회 중</h4>
                    <p class="text-yellow-600 text-sm">${message}</p>
                </div>
            </div>
        </div>
    `;
    conversationHistory.insertAdjacentHTML('beforeend', statusHtml);
}

// 빠른 조회 결과 표시 (수정된 버전)
function displayQuickResults(data) {
    // "데이터 조회 중" 상태 메시지 제거
    const dataQueryStatus = document.getElementById('dataQueryStatus');
    if (dataQueryStatus) {
        dataQueryStatus.remove();
    }

    // 간단한 테이블 결과만 표시
    const resultHtml = `
        <div id="queryResults" class="mt-4">
            <div class="table-container">
                ${createTable(data.data)}
            </div>

            <div class="success">
                <h3>✅ 조회 완료</h3>
                <p>총 ${data.row_count}개의 결과를 성공적으로 조회했습니다.</p>
                <p>💡 이제 아래 <strong>"고급 분석 옵션"</strong>을 사용하여 더 자세한 인사이트를 얻어보세요!</p>
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 0.5rem; border-left: 4px solid #3b82f6;">
                    <p style="margin: 0; font-size: 0.875rem;">
                        🔍 <strong>다음 단계:</strong> 
                        고급 분석 옵션이 활성화되었습니다. "구조화 분석"으로 AI 리포트와 차트를, 
                        "창의적 HTML"로 완전한 분석 문서를 생성할 수 있습니다.
                    </p>
                </div>
            </div>
        </div>
    `;

    // 기존 내용에 결과를 추가
    conversationHistory.insertAdjacentHTML('beforeend', resultHtml);
    
    // 결과 섹션으로 부드러운 스크롤
    setTimeout(() => {
        document.getElementById('queryResults').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 100);
}

// 구조화된 분석 결과 표시
function displayStructuredResults(data) {
    const resultHtml = `
        <div class="results-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid #e5e7eb;">
            <h2 style="font-size: 1.5rem; font-weight: 600; color: #374151; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                📊 구조화 분석 결과 
                <span style="background: #3b82f6; color: white; padding: 0.25rem 0.5rem; border-radius: 0.75rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-left: 0.75rem;">STRUCTURED</span>
            </h2>
            <div style="color: #6b7280; font-size: 0.875rem; font-weight: 500;">${data.row_count.toLocaleString()}개 결과</div>
        </div>

        ${data.data_summary ? createDataSummary(data.data_summary, data.row_count) : ''}

        <div style="background: #f0fdf4; padding: 1.25rem; border-radius: 0.75rem; margin-bottom: 1.25rem; border-left: 4px solid #10b981;">
            <h3 style="margin-bottom: 1rem; color: #374151; font-size: 1.125rem; font-weight: 600;">🤖 AI 분석 리포트</h3>
            <div style="margin-top: 1rem; line-height: 1.6;">
                ${parseMarkdown(data.analysis_report)}
            </div>
        </div>

        ${data.chart_config ? `
        <div style="background: white; padding: 1.25rem; border-radius: 0.75rem; margin-top: 1.25rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb;">
            <h4 style="margin-bottom: 1rem; color: #374151; text-align: center; font-size: 1.125rem; font-weight: 500;">${data.chart_config.title || '데이터 시각화'}</h4>
            <div style="position: relative; width: 100%; height: 400px;">
                <canvas id="analysisChart" style="max-height: 400px;"></canvas>
            </div>
        </div>
        ` : ''}

        <div class="table-container" style="margin-top: 1.5rem;">
            ${createTable(data.data)}
        </div>

        <div class="success">
            <h3>✅ 구조화 분석 완료</h3>
            <p>총 ${data.row_count.toLocaleString()}개의 결과를 AI가 심층 분석했습니다.</p>
            <p>🤖 위의 AI 분석 리포트와 차트에서 핵심 인사이트를 확인하세요.</p>
            <p>📄 더 상세한 문서가 필요하다면 "창의적 HTML" 옵션을 사용해보세요.</p>
        </div>
    `;

    resultsSection.innerHTML = resultHtml;
    
    // 차트 생성 (있는 경우)
    if (data.chart_config) {
        setTimeout(() => createChart(data.data, data.chart_config), 100);
    }
    
    // 결과 섹션으로 스크롤
    setTimeout(() => {
        resultsSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 100);
}

// 창의적 HTML 결과 표시
function displayCreativeHtmlResults(data) {
    const qualityBadge = data.quality_score >= 80 ? 
        `<span style="background: #34a853; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">고품질</span>` :
        data.quality_score >= 60 ?
        `<span style="background: #ffa726; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">양호</span>` :
        `<span style="background: #ff6b6b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">기본</span>`;

    const resultHtml = `
        <div class="results-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid #e5e7eb;">
            <h2 style="font-size: 1.5rem; font-weight: 600; color: #374151; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                🎨 창의적 HTML 리포트 
                <span style="background: #ef4444; color: white; padding: 0.25rem 0.5rem; border-radius: 0.75rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-left: 0.75rem;">CREATIVE</span>
            </h2>
            <div style="color: #6b7280; font-size: 0.875rem; font-weight: 500;">${data.row_count}개 결과 • ${qualityBadge}</div>
        </div>
        
        <div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
            <button onclick="openInNewWindow()" style="padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid #d1d5db; background: white; color: #374151; font-weight: 500; cursor: pointer; transition: all 0.2s ease;">🔗 새 창에서 열기</button>
            <button onclick="downloadHtml()" style="padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid #d1d5db; background: white; color: #374151; font-weight: 500; cursor: pointer; transition: all 0.2s ease;">💾 HTML 다운로드</button>
            ${data.is_fallback ? '<button onclick="regenerateHtml()" style="padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid #d1d5db; background: white; color: #374151; font-weight: 500; cursor: pointer; transition: all 0.2s ease;">🔄 재생성</button>' : ''}
        </div>
        
        ${data.is_fallback ? `
        <div style="background: #fffbeb; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f59e0b; color: #92400e; margin-bottom: 1rem;">
            ⚠️ <strong>알림:</strong> 고급 HTML 생성에 실패하여 기본 형태로 표시됩니다. 재생성을 시도해보세요.
        </div>
        ` : ''}
        
        <div style="border-radius: 0.5rem; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
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
            <p>🔗 "새 창에서 열기"로 전체 화면에서 보거나, "HTML 다운로드"로 저장할 수 있습니다.</p>
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
    
    // 결과 섹션으로 스크롤
    setTimeout(() => {
        resultsSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 100);
}

// 데이터 요약 섹션 생성
function createDataSummary(dataSummary, rowCount) {
    const overview = dataSummary.overview || {};
    const insights = dataSummary.quick_insights || [];
    
    return `
        <div style="background: #f0fdf4; padding: 1.25rem; border-radius: 0.75rem; margin-bottom: 1.25rem; border-left: 4px solid #10b981;">
            <h3 style="margin-bottom: 1rem; color: #374151; font-size: 1.125rem; font-weight: 600;">📊 데이터 개요</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                <div style="background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; text-align: center;">
                    <h4 style="color: #3b82f6; margin-bottom: 0.25rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">총 레코드</h4>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #374151;">${(overview.total_rows || rowCount).toLocaleString()}</div>
                    <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">개</div>
                </div>
                <div style="background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; text-align: center;">
                    <h4 style="color: #3b82f6; margin-bottom: 0.25rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">컬럼 수</h4>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #374151;">${overview.columns_count || 0}</div>
                    <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">개</div>
                </div>
                <div style="background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; text-align: center;">
                    <h4 style="color: #3b82f6; margin-bottom: 0.25rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">숫자형 컬럼</h4>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #374151;">${Object.values(overview.data_types || {}).filter(type => type === 'numeric').length}</div>
                    <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">개</div>
                </div>
                <div style="background: white; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e5e7eb; text-align: center;">
                    <h4 style="color: #3b82f6; margin-bottom: 0.25rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">카테고리형 컬럼</h4>
                    <div style="font-size: 1.5rem; font-weight: 600; color: #374151;">${Object.values(overview.data_types || {}).filter(type => type === 'categorical').length}</div>
                    <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">개</div>
                </div>
            </div>
            ${insights && insights.length > 0 ? `
            <div style="margin-top: 1.5rem;">
                <h4 style="color: #374151; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">🎯 핵심 인사이트</h4>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem; color: #374151;">
                    ${insights.map(insight => `<li style="margin-bottom: 0.5rem;">${insight}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
    `;
}

// 차트 생성 함수 (Chart.js 사용)
function createChart(data, config) {
    const canvas = document.getElementById('analysisChart');
    if (!canvas || !data || data.length === 0) return;
    
    // 기존 차트 제거
    if (window.currentChart) {
        window.currentChart.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    
    let chartData = {};
    let chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 20
                }
            },
            title: {
                display: true,
                text: config.title || '데이터 시각화',
                font: {
                    size: 16,
                    weight: 'bold'
                },
                padding: 20
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
        }
    };
    
    if (config.type === 'bar' && config.label_column && config.value_column) {
        // 막대 차트
        const labels = data.slice(0, 20).map(row => String(row[config.label_column])); // 상위 20개만
        const values = data.slice(0, 20).map(row => Number(row[config.value_column]) || 0);
        
        chartData = {
            labels: labels,
            datasets: [{
                label: config.value_column,
                data: values,
                backgroundColor: 'rgba(66, 133, 244, 0.8)',
                borderColor: 'rgba(66, 133, 244, 1)',
                borderWidth: 2,
                borderRadius: 4,
                borderSkipped: false,
            }]
        };
        
        chartOptions.scales = {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        };
    }
    
    // 차트 생성
    try {
        window.currentChart = new Chart(ctx, {
            type: config.type,
            data: chartData,
            options: chartOptions
        });
    } catch (error) {
        console.error('차트 생성 오류:', error);
    }
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

    // 행 생성 (최대 50개까지만 표시)
    const displayData = data.slice(0, 50);
    const rowsHtml = displayData.map(row => {
        const cellsHtml = headers.map(header => {
            const value = row[header];
            return `<td>${formatCellValue(value)}</td>`;
        }).join('');
        return `<tr>${cellsHtml}</tr>`;
    }).join('');

    const hasMoreData = data.length > 50;
    const moreDataMessage = hasMoreData ? 
        `<div style="text-align: center; padding: 1rem; background: #f9fafb; color: #6b7280; border-radius: 0 0 0.75rem 0.75rem;">📊 ${data.length}개 중 50개만 표시됩니다. 전체 결과를 보려면 "창의적 HTML" 모드를 사용하세요.</div>` : '';

    return `
        <table>
            <thead>
                <tr>${headerHtml}</tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
        ${moreDataMessage}
    `;
}

// 셀 값 포맷팅
function formatCellValue(value) {
    if (value === null || value === undefined) {
        return '<em style="color: #999;">NULL</em>';
    }
    
    if (typeof value === 'number') {
        return value.toLocaleString();
    }
    
    if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
        try {
            const date = new Date(value);
            return date.toLocaleDateString('ko-KR');
        } catch (e) {
            return escapeHtml(value);
        }
    }
    
    const stringValue = String(value);
    if (stringValue.length > 100) {
        return `<span title="${escapeHtml(stringValue)}">${escapeHtml(stringValue.substring(0, 100))}...</span>`;
    }
    
    return escapeHtml(stringValue);
}

// 마크다운 파싱
function parseMarkdown(text) {
    if (!text) return '';
    
    return text
        .replace(/### (.*$)/gim, '<h3 style="margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.125rem; font-weight: 600; color: #374151;">$1</h3>')
        .replace(/## (.*$)/gim, '<h2 style="margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.25rem; font-weight: 600; color: #374151;">$1</h2>')
        .replace(/# (.*$)/gim, '<h1 style="margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.375rem; font-weight: 600; color: #374151;">$1</h1>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong style="color: #1e40af;">$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/`(.*?)`/gim, '<code style="background: #e5e7eb; padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-size: 0.875rem; font-family: ui-monospace, monospace;">$1</code>')
        .replace(/^\* (.*$)/gim, '<li style="margin-bottom: 0.25rem;">$1</li>')
        .replace(/^- (.*$)/gim, '<li style="margin-bottom: 0.25rem;">$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li style="margin-bottom: 0.25rem;">$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul style="margin: 0.75rem 0; margin-left: 1.25rem;">$1</ul>')
        .replace(/\n\n/gim, '</p><p style="margin-bottom: 1rem;">')
        .replace(/^(?!<)/gim, '<p style="margin-bottom: 1rem;">')
        .replace(/$/gim, '</p>');
}

// 오류 표시
function displayError(errorMessage, mode) {
    const modeLabels = {
        'quick': '조회',
        'structured': '구조화 분석',
        'creative': '창의적 HTML'
    };

    const errorHtml = `
        <div class="error">
            <h3>❌ ${modeLabels[mode]} 오류 발생</h3>
            <p>${escapeHtml(errorMessage)}</p>
            <div style="margin-top: 1rem;">
                <p><small>💡 문제 해결 방법:</small></p>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                    <li>질문을 더 구체적으로 작성해보세요</li>
                    <li>다른 예시 질문을 시도해보세요</li>
                    <li>서버 로그를 확인하거나 관리자에게 문의하세요</li>
                </ul>
            </div>
        </div>
    `;

    conversationHistory.insertAdjacentHTML('beforeend', errorHtml);
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 페이지 로드 시 초기화
window.addEventListener('load', function() {
    questionInput.focus();
    
    // 마지막 질문 복원
    const lastQuestion = localStorage.getItem('ga4_last_question');
    if (lastQuestion && lastQuestion.trim()) {
        questionInput.value = lastQuestion;
    }
});

// 자동 저장 기능
questionInput.addEventListener('input', function() {
    localStorage.setItem('ga4_last_question', this.value);
    
    // 새로운 입력 시 고급 분석 옵션 숨기기
    if (analysisOptions && analysisOptions.classList.contains('show')) {
        analysisOptions.classList.remove('show');
        structuredBtn.disabled = true;
        creativeBtn.disabled = true;
        lastQuickQueryData = null;
    }
});

// 키보드 단축키 지원
document.addEventListener('keydown', function(e) {
    if (e.altKey && e.key === '1') {
        e.preventDefault();
        if (!quickBtn.disabled) executeQuery('quick');
    } else if (e.altKey && e.key === '2') {
        e.preventDefault();
        if (!structuredBtn.disabled) executeQuery('structured');
    } else if (e.altKey && e.key === '3') {
        e.preventDefault();
        if (!creativeBtn.disabled) executeQuery('creative');
    } else if (e.key === 'Escape' && document.activeElement === questionInput) {
        questionInput.value = '';
        localStorage.removeItem('ga4_last_question');
    }
});

// 질문 입력창 이벤트
questionInput.addEventListener('focus', function() {
    if (!this.value) {
        const examples = [
            "오늘 총 이벤트 수를 알려주세요",
            "가장 인기 있는 이벤트 유형을 보여주세요",
            "국가별 사용자 분포를 보여주세요",
            "모바일 사용자 비율을 알려주세요",
            "시간대별 활동량을 보여주세요",
            "구매 관련 이벤트를 분석해주세요",
            "트래픽 소스별 성과를 보여주세요",
            "운영체제별 사용자 현황을 알려주세요"
        ];
        this.placeholder = examples[Math.floor(Math.random() * examples.length)];
    }
});

questionInput.addEventListener('blur', function() {
    if (!this.value) {
        this.placeholder = "예: 한국 사용자들의 page_view 이벤트 수를 알려주세요";
    }
});

// 처리 과정 모니터링을 위한 추가 함수들
function showProcessingSteps(mode) {
    if (mode === 'structured') {
        // 구조화 분석용 간단한 로딩 표시
        const loadingHtml = `
            <div style="text-align: center; padding: 2rem; background: #f0f9ff; border-radius: 0.75rem; margin: 1rem 0;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #e5e7eb; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <h3 style="margin: 1rem 0 0.5rem 0; color: #374151;">📊 구조화 분석 진행 중</h3>
                <p style="color: #6b7280; margin: 0;">AI가 데이터를 심층 분석하고 차트를 생성하고 있습니다...</p>
                <p style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.5rem;">이 과정은 30초 정도 소요됩니다.</p>
            </div>
        `;
        resultsSection.innerHTML = loadingHtml;
    } else if (mode === 'creative') {
        // 창의적 HTML용 로딩 표시
        const loadingHtml = `
            <div style="text-align: center; padding: 2rem; background: #fef7f0; border-radius: 0.75rem; margin: 1rem 0;">
                <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #fed7aa; border-top-color: #f59e0b; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <h3 style="margin: 1rem 0 0.5rem 0; color: #374151;">🎨 창의적 HTML 생성 중</h3>
                <p style="color: #6b7280; margin: 0;">Claude가 독립적인 HTML 분석 리포트를 생성하고 있습니다...</p>
                <p style="color: #9ca3af; font-size: 0.875rem; margin-top: 0.5rem;">고품질 리포트 생성을 위해 최대 1분 정도 소요될 수 있습니다.</p>
            </div>
        `;
        resultsSection.innerHTML = loadingHtml;
    }
}

// 로딩 상태 개선
function setLoadingState(isLoading, mode = '') {
    quickBtn.disabled = isLoading;
    
    if (mode !== 'quick') {
        structuredBtn.disabled = isLoading;
        creativeBtn.disabled = isLoading;
    }
    
    if (isLoading) {
        if (mode === 'quick') {
            quickBtn.innerHTML = '<span class="btn-main-text">⏳ 조회 중...</span><div class="btn-description">잠시만 기다려주세요</div>';
        } else if (mode === 'structured') {
            structuredBtn.innerHTML = '<span class="btn-main-text">⏳ 분석 중...</span><div class="btn-description">AI가 분석하고 있습니다</div>';
            showProcessingSteps(mode);
        } else if (mode === 'creative') {
            creativeBtn.innerHTML = '<span class="btn-main-text">⏳ 생성 중...</span><div class="btn-description">HTML 리포트 생성 중</div>';
            showProcessingSteps(mode);
        }
    } else {
        // 원래 버튼 텍스트 복원
        quickBtn.innerHTML = `
            <span class="btn-main-text">⚡ 빠른 조회</span>
            <div class="btn-description">데이터를 먼저 확인해보세요</div>
        `;
        structuredBtn.innerHTML = `
            <span class="btn-main-text">📊 구조화 분석</span>
            <div class="btn-description">차트 + AI 리포트 생성</div>
        `;
        creativeBtn.innerHTML = `
            <span class="btn-main-text">🎨 창의적 HTML</span>
            <div class="btn-description">독립 문서 생성</div>
        `;
    }
}

// 스타일 추가 (CSS 애니메이션용)
const additionalStyles = `
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .slide-down {
            animation: slideDown 0.3s ease-out;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
`;

// 스타일을 head에 추가
document.head.insertAdjacentHTML('beforeend', additionalStyles);