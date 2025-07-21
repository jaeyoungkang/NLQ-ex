const UI = {
    // 정보 박스 렌더링
    renderInfoBox() {
        const infoBox = document.getElementById('infoBox');
        infoBox.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-google-blue mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                    </svg>
                </div>
                <div class="ml-3 text-sm">
                    <p class="font-medium text-gray-800">
                        <span class="font-semibold">📊 데이터:</span> 2020.11.21 GA4 이벤트 데이터 | 
                        <span class="font-semibold">🏢 테이블:</span> nlq-ex.test_dataset.events_20201121 | 
                        <span class="font-semibold">🤖 AI:</span> Claude Sonnet 4 + BigQuery
                    </p>
                </div>
            </div>
        `;
    },

    // 질문 섹션 렌더링
    renderQuerySection() {
        const querySection = document.getElementById('querySection');
        querySection.innerHTML = `
            <div class="mb-6">
                <label for="question" class="block text-lg font-medium text-gray-700 mb-3">질문을 입력하세요</label>
                <textarea id="question" rows="4" class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-google-blue focus:border-google-blue transition-all duration-200 resize-y font-medium placeholder-gray-400" placeholder="예: 한국 사용자들의 페이지뷰 이벤트는 몇 개인가요?"></textarea>
            </div>
            ${this.renderModeSelector()}
            ${this.renderActionButtons()}
        `;
    },

    // 모드 선택기 렌더링
    renderModeSelector() {
        return `
            <div class="mb-6">
                <h3 class="text-lg font-medium text-gray-700 mb-4">분석 모드 선택</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="mode-card cursor-pointer p-5 border-2 border-gray-200 rounded-xl card-hover mode-selected" data-mode="quick" onclick="selectMode('quick')">
                        <div class="flex items-center mb-3">
                            <span class="text-2xl mr-3">⚡</span>
                            <h4 class="text-lg font-semibold text-google-blue">빠른 조회</h4>
                        </div>
                        <p class="text-gray-600 mb-3 text-sm">SQL 실행 후 데이터만 즉시 확인</p>
                        <ul class="text-xs text-green-600 space-y-1">
                            <li class="flex items-center"><span class="mr-1">✓</span> 즉시 결과</li>
                            <li class="flex items-center"><span class="mr-1">✓</span> 테이블 형태</li>
                            <li class="flex items-center"><span class="mr-1">✓</span> 간단한 분석</li>
                        </ul>
                    </div>
                    <div class="mode-card cursor-pointer p-5 border-2 border-gray-200 rounded-xl card-hover" data-mode="structured" onclick="selectMode('structured')">
                        <div class="flex items-center mb-3">
                            <span class="text-2xl mr-3">📊</span>
                            <h4 class="text-lg font-semibold text-google-blue">구조화 분석</h4>
                        </div>
                        <p class="text-gray-600 mb-3 text-sm">데이터 + 차트 + AI 분석 리포트</p>
                        <ul class="text-xs text-green-600 space-y-1">
                            <li class="flex items-center"><span class="mr-1">✓</span> 자동 차트 생성</li>
                            <li class="flex items-center"><span class="mr-1">✓</span> AI 인사이트</li>
                            <li class="flex items-center"><span class="mr-1">✓</span> 비즈니스 제안</li>
                        </ul>
                    </div>
                    <div class="mode-card cursor-pointer p-5 border-2 border-gray-200 rounded-xl card-hover" data-mode="creative" onclick="selectMode('creative')">
                        <div class="flex items-center mb-3">
                            <span class="text-2xl mr-3">🎨</span>
                            <h4 class="text-lg font-semibold text-google-blue">창의적 HTML</h4>
                        </div>
                        <p class="text-gray-600 mb-3 text-sm">완전한 독립 HTML 리포트 생성</p>
                        <ul class="text-xs text-green-600 space-y-1">
                            <li class="flex items-center"><span class="mr-1">✓</span> 창의적 디자인</li>
                            <li class="flex items-center"><span class="mr-1">✓</span> 다운로드 가능</li>
                            <li class="flex items-center"><span class="mr-1">✓</span> 프레젠테이션용</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    },

    // 액션 버튼 렌더링
    renderActionButtons() {
        return `
            <div class="flex items-center gap-4 flex-wrap">
                <button id="executeBtn" class="bg-google-blue hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium btn-hover flex items-center gap-2 transition-all duration-200">
                    <span class="text-lg">🚀</span>
                    <span>분석 실행</span>
                </button>
                <div id="loading" class="hidden flex items-center gap-2 text-gray-600">
                    <div class="w-4 h-4 spinner"></div>
                    <span id="loadingText" class="text-sm">분석 중...</span>
                </div>
                <div class="text-xs text-gray-500 hidden md:flex items-center gap-4">
                    <kbd class="px-2 py-1 bg-gray-100 rounded text-xs">Ctrl + Enter</kbd>
                    <kbd class="px-2 py-1 bg-gray-100 rounded text-xs">Alt + 1,2,3</kbd>
                </div>
            </div>
        `;
    },

    // 예시 섹션 렌더링
    renderExamplesSection() {
        const examplesSection = document.getElementById('examplesSection');
        examplesSection.innerHTML = `
            <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span>💡</span>
                예시 질문들 <span class="text-sm text-gray-500 font-normal">(클릭하면 자동 입력)</span>
            </h3>
            ${Examples.renderAll()}
        `;
    },

    // 모드 선택 업데이트
    updateModeSelection(mode) {
        document.querySelectorAll('.mode-card').forEach(card => {
            card.classList.remove('mode-selected');
            if (card.dataset.mode === mode) {
                card.classList.add('mode-selected');
            }
        });
    },

    // 실행 버튼 업데이트
    updateExecuteButton(mode) {
        const modeConfig = {
            quick: { icon: '⚡', text: '빠른 조회' },
            structured: { icon: '📊', text: '구조화 분석' },
            creative: { icon: '🎨', text: 'HTML 생성' }
        };
        
        const config = modeConfig[mode];
        const btn = document.getElementById('executeBtn');
        btn.innerHTML = `
            <span class="text-lg">${config.icon}</span>
            <span>${config.text}</span>
        `;
    },

    // 로딩 상태 설정
    setLoading(isLoading, mode = '') {
        const executeBtn = document.getElementById('executeBtn');
        const loading = document.getElementById('loading');
        const loadingText = document.getElementById('loadingText');
        
        executeBtn.disabled = isLoading;
        
        if (isLoading) {
            loading.classList.remove('hidden');
            executeBtn.classList.add('opacity-50', 'cursor-not-allowed');
            
            const messages = {
                quick: '빠르게 데이터를 조회하고 있습니다...',
                structured: 'AI가 데이터를 분석하고 있습니다...',
                creative: 'HTML 리포트를 생성하고 있습니다...'
            };
            loadingText.textContent = messages[mode] || '처리 중...';
        } else {
            loading.classList.add('hidden');
            executeBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    },

    // 메시지 표시
    showMessage(message, type) {
        const container = document.getElementById('messageContainer');
        const messageDiv = document.createElement('div');
        
        const bgColor = type === 'error' ? 'bg-red-100 border-red-400 text-red-700' : 'bg-green-100 border-green-400 text-green-700';
        const icon = type === 'error' ? '❌' : '✅';
        
        messageDiv.className = `${bgColor} border px-4 py-3 rounded-lg shadow-lg mb-4 fade-in`;
        messageDiv.innerHTML = `
            <div class="flex items-start">
                <span class="mr-2">${icon}</span>
                <span class="text-sm font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-lg leading-none">&times;</button>
            </div>
        `;
        
        container.appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    },

    // 입력창 하이라이트
    highlightInput(input) {
        input.classList.add('ring-2', 'ring-google-blue', 'ring-opacity-50');
        setTimeout(() => {
            input.classList.remove('ring-2', 'ring-google-blue', 'ring-opacity-50');
        }, 1000);
    },

    // 결과 표시 관련 메서드들...
    showResults() {
        document.getElementById('results').classList.remove('hidden');
    },

    updateResultsHeader(data) {
        const modeLabels = {
            quick: '⚡ 빠른 조회',
            structured: '📊 구조화 분석',
            creative: '🎨 창의적 HTML'
        };
        
        // 결과 헤더 업데이트 로직
    },

    scrollToResults() {
        document.getElementById('results').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }

    // 추가 메서드들은 필요에 따라 구현...
};