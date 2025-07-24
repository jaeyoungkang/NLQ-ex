// main.js - 핵심 대화 로직만 담당
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const charCounter = document.getElementById('charCounter');
const messagesContainer = document.getElementById('messagesContainer');

let isProcessing = false;
let messageIdCounter = 0;

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    messageInput.focus();
    updateCharCount();
});

// 예시 질문 설정
function setQuestion(question) {
    messageInput.value = question;
    messageInput.focus();
    updateCharCount();
    autoResize();
}

// 문자 수 카운트 및 버튼 상태 업데이트
function updateCharCount() {
    const count = messageInput.value.length;
    charCounter.textContent = `${count}/2000`;
    sendButton.disabled = count === 0 || count > 2000 || isProcessing;
}

// 자동 리사이즈
function autoResize() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// 이벤트 리스너
messageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendButton.disabled) sendMessage();
    }
});

messageInput.addEventListener('input', function() {
    updateCharCount();
    autoResize();
});

sendButton.addEventListener('click', sendMessage);

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.activeElement === messageInput) {
        messageInput.value = '';
        updateCharCount();
        autoResize();
    }
});

// 메시지 전송
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || message.length > 2000 || isProcessing) return;
    
    isProcessing = true;
    updateUIState();
    
    addUserMessage(message);
    messageInput.value = '';
    updateCharCount();
    autoResize();
    
    try {
        const analysisDecision = await requestAnalysisDecision(message);
        if (analysisDecision.needsAnalysis) {
            await showAnalysisOptions(message);
        } else {
            await executeSimpleQuery(message);
        }
    } catch (error) {
        addAssistantMessage(`처리 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        isProcessing = false;
        updateUIState();
    }
}

// UI 상태 업데이트
function updateUIState() {
    updateCharCount();
    sendButton.innerHTML = isProcessing ? 
        `<div class="typing-dots"><span></span><span></span><span></span></div>` :
        `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

// 사용자 메시지 추가
function addUserMessage(message) {
    const messageHtml = `
        <div class="message">
            <div class="user-message">
                <div class="message-content">${escapeHtml(message)}</div>
            </div>
        </div>`;
    messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
    scrollToBottom();
}

// AI 메시지 추가
function addAssistantMessage(content, showTyping = false) {
    const messageId = `message-${++messageIdCounter}`;
    const messageHtml = `
        <div class="message" id="${messageId}">
            <div class="assistant-message">
                <div class="message-content">
                    <div class="flex items-start">
                        <div class="w-6 h-6 rounded-full bg-claude-accent text-white text-xs flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">AI</div>
                        <div class="flex-1" id="${messageId}-content">
                            ${showTyping ? '<div class="typing-indicator">생각하는 중<div class="typing-dots"><span></span><span></span><span></span></div></div>' : content}
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
    messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
    scrollToBottom();
    return messageId;
}

// 메시지 업데이트
function updateMessage(messageId, content) {
    const contentElement = document.getElementById(`${messageId}-content`);
    if (contentElement) {
        contentElement.innerHTML = content;
        scrollToBottom();
    }
}

// 스크롤
function scrollToBottom() {
    setTimeout(() => messagesContainer.scrollTop = messagesContainer.scrollHeight, 100);
}

// 분석 유형 판단
async function requestAnalysisDecision(question) {
    const messageId = addAssistantMessage('', true);
    const analysisKeywords = ['분석', '비교', '트렌드', '패턴', '인사이트', '리포트', '차트', '시각화'];
    const needsAnalysis = analysisKeywords.some(keyword => question.includes(keyword));
    
    await sleep(1500);
    
    if (needsAnalysis) {
        updateMessage(messageId, `
            질문을 분석해보니 더 깊이 있는 분석이 도움이 될 것 같습니다.<br><br>
            어떤 방식으로 분석을 진행할까요?
            <div class="analysis-buttons">
                <button class="analysis-btn" onclick="executeAnalysis('${escapeHtml(question)}', 'quick')">📊 기본 조회</button>
                <button class="analysis-btn" onclick="executeAnalysis('${escapeHtml(question)}', 'structured')">📈 구조화 분석</button>
                <button class="analysis-btn" onclick="executeAnalysis('${escapeHtml(question)}', 'creative')">🎨 HTML 리포트</button>
            </div>`);
        return { needsAnalysis: true };
    } else {
        document.getElementById(messageId).remove();
        return { needsAnalysis: false };
    }
}

// 분석 옵션 제시
async function showAnalysisOptions(message) {
    // requestAnalysisDecision에서 처리됨
}

// 분석 실행 (전역 함수)
window.executeAnalysis = async function(question, analysisType) {
    document.querySelectorAll('.analysis-btn').forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.5';
    });
    
    isProcessing = true;
    updateUIState();
    
    try {
        if (analysisType === 'quick') await executeSimpleQuery(question);
        else if (analysisType === 'structured') await executeStructuredAnalysis(question);
        else if (analysisType === 'creative') await executeCreativeAnalysis(question);
    } catch (error) {
        addAssistantMessage(`분석 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        isProcessing = false;
        updateUIState();
    }
};

// 유틸리티 함수
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}