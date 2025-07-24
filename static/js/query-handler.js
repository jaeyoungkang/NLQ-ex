// query-handler.js - 쿼리 실행 및 분석 처리

// 단순 조회 실행
async function executeSimpleQuery(question) {
    const messageId = addAssistantMessage('', true);
    
    try {
        updateMessage(messageId, '쿼리를 생성하고 있습니다...');
        
        const response = await fetch('/quick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // 쿼리 결과 저장 (구조화 분석용)
            window.lastQueryData = {
                question: question,
                sql: data.generated_sql,
                data: data.data,
                rowCount: data.row_count,
                timestamp: Date.now()
            };
            
            updateMessage(messageId, `
                ✅ SQL 쿼리가 생성되었습니다:
                <div class="bg-gray-100 border border-gray-200 rounded-lg p-3 my-3 overflow-x-auto">
                    <code class="text-sm font-mono whitespace-pre-wrap">${escapeHtml(data.generated_sql)}</code>
                </div>
                데이터를 조회하고 있습니다...
            `);
            
            await sleep(1000);
            
            updateMessage(messageId, `
                ✅ 조회가 완료되었습니다. (총 ${data.row_count}개 결과)
                <div class="bg-gray-100 border border-gray-200 rounded-lg p-3 my-3 overflow-x-auto">
                    <code class="text-sm font-mono whitespace-pre-wrap">${escapeHtml(data.generated_sql)}</code>
                </div>
                <div class="mt-4">${createTable(data.data)}</div>
                
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                    <p class="text-sm text-blue-800">
                        💡 <strong>다음 단계:</strong> 이제 "구조화 분석"으로 이 데이터에 대한 상세한 인사이트를 얻어보세요!
                    </p>
                </div>
            `);
            
        } else {
            updateMessage(messageId, `❌ 오류가 발생했습니다: ${data.error || '쿼리 생성에 실패했습니다.'}`);
        }
        
    } catch (error) {
        updateMessage(messageId, `❌ 네트워크 오류: ${error.message}`);
    }
}

// 구조화 분석 실행 (새로운 로직)
async function executeStructuredAnalysis(question) {
    const messageId = addAssistantMessage('', true);
    
    // 1. 이전 쿼리 결과 확인
    if (!window.lastQueryData || !window.lastQueryData.data || window.lastQueryData.data.length === 0) {
        updateMessage(messageId, `
            📊 구조화 분석을 위해서는 먼저 데이터를 조회해야 합니다.
            
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 my-4">
                <h4 class="font-semibold text-blue-800 mb-2">🔍 분석 절차</h4>
                <ol class="list-decimal list-inside space-y-2 text-sm text-blue-700">
                    <li>먼저 <strong>"기본 조회"</strong>로 데이터를 확인하세요</li>
                    <li>조회 결과를 바탕으로 구조화 분석을 수행합니다</li>
                    <li>데이터 패턴과 인사이트를 자동으로 분석해드립니다</li>
                </ol>
            </div>
            
            <button class="analysis-btn" onclick="executeAnalysis('${escapeHtml(question)}', 'quick')">
                📊 먼저 기본 조회 실행하기
            </button>
        `);
        return;
    }
    
    // 2. 쿼리 결과 기반 분석 수행
    try {
        updateMessage(messageId, '조회된 데이터를 분석하고 있습니다...');
        await sleep(1500);
        
        const analysis = analyzeQueryResults(window.lastQueryData.data);
        const suggestions = generateAnalysisSuggestions(analysis, window.lastQueryData.question);
        
        updateMessage(messageId, `
            ✅ 구조화 분석이 완료되었습니다.
            
            ${createDataProfile(analysis, window.lastQueryData)}
            ${createBasicComments(analysis)}
            ${createInsightsAndSuggestions(suggestions)}
            
            <div class="mt-4">
                <h4 class="font-semibold text-gray-800 mb-2">📊 분석 대상 데이터</h4>
                ${createTable(window.lastQueryData.data)}
            </div>
        `);
        
    } catch (error) {
        updateMessage(messageId, `❌ 분석 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 쿼리 결과 분석 함수
function analyzeQueryResults(data) {
    if (!data || data.length === 0) return null;
    
    const columns = Object.keys(data[0]);
    const analysis = {
        totalRows: data.length,
        columns: columns,
        columnAnalysis: {}
    };
    
    // 각 컬럼별 분석
    columns.forEach(col => {
        const values = data.map(row => row[col]).filter(val => val !== null && val !== undefined);
        const uniqueValues = [...new Set(values)];
        
        analysis.columnAnalysis[col] = {
            type: typeof values[0],
            uniqueCount: uniqueValues.length,
            nullCount: data.length - values.length,
            completeness: Math.round((values.length / data.length) * 100),
            topValues: getTopValues(values, 5)
        };
        
        // 숫자형 컬럼 추가 분석
        if (typeof values[0] === 'number') {
            analysis.columnAnalysis[col].sum = values.reduce((a, b) => a + b, 0);
            analysis.columnAnalysis[col].avg = Math.round(analysis.columnAnalysis[col].sum / values.length);
            analysis.columnAnalysis[col].min = Math.min(...values);
            analysis.columnAnalysis[col].max = Math.max(...values);
        }
    });
    
    return analysis;
}

// 상위 값들 추출
function getTopValues(values, limit = 5) {
    const counts = {};
    values.forEach(val => {
        counts[val] = (counts[val] || 0) + 1;
    });
    
    return Object.entries(counts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, limit)
        .map(([value, count]) => ({ value, count, percentage: Math.round((count / values.length) * 100) }));
}

// 데이터 프로파일 생성
function createDataProfile(analysis, queryData) {
    const timeAgo = Math.round((Date.now() - queryData.timestamp) / 1000);
    
    return `
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 my-4">
            <h4 class="font-semibold text-gray-800 mb-3">📋 조회된 데이터 분석</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-600">${analysis.totalRows.toLocaleString()}</div>
                    <div class="text-gray-600">총 레코드</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">${analysis.columns.length}</div>
                    <div class="text-gray-600">컬럼 수</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-purple-600">${Object.values(analysis.columnAnalysis).filter(col => col.type === 'string').length}</div>
                    <div class="text-gray-600">문자형</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-orange-600">${Object.values(analysis.columnAnalysis).filter(col => col.type === 'number').length}</div>
                    <div class="text-gray-600">숫자형</div>
                </div>
            </div>
            <div class="mt-3 text-xs text-gray-500">
                📝 원본 질문: "${queryData.question}" (${timeAgo}초 전 조회)
            </div>
        </div>
    `;
}

// 기본 코멘트 생성
function createBasicComments(analysis) {
    const comments = [];
    
    // 데이터 규모 코멘트
    if (analysis.totalRows > 10000) {
        comments.push(`대용량 데이터셋입니다 (${analysis.totalRows.toLocaleString()}개). 통계적 신뢰성이 높습니다.`);
    } else if (analysis.totalRows < 100) {
        comments.push(`소규모 데이터셋입니다 (${analysis.totalRows}개). 추가 데이터 수집을 고려해보세요.`);
    }
    
    // 컬럼별 코멘트
    Object.entries(analysis.columnAnalysis).forEach(([col, stats]) => {
        if (stats.type === 'string') {
            const topValue = stats.topValues[0];
            if (topValue.percentage > 50) {
                comments.push(`'${col}' 컬럼: '${topValue.value}'가 ${topValue.percentage}%로 압도적입니다.`);
            } else if (stats.uniqueCount === analysis.totalRows) {
                comments.push(`'${col}' 컬럼: 모든 값이 고유합니다 (ID 성격).`);
            }
        }
        
        if (stats.type === 'number') {
            comments.push(`'${col}' 컬럼: 총합 ${stats.sum.toLocaleString()}, 평균 ${stats.avg.toLocaleString()}`);
        }
        
        if (stats.completeness < 100) {
            comments.push(`'${col}' 컬럼: ${100 - stats.completeness}%의 NULL 값이 있습니다.`);
        }
    });
    
    return `
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 my-4">
            <h4 class="font-semibold text-blue-800 mb-3">💭 데이터 특성 분석</h4>
            <ul class="space-y-2 text-sm text-blue-700">
                ${comments.map(comment => `<li>• ${comment}</li>`).join('')}
            </ul>
        </div>
    `;
}

// 인사이트 및 제안 생성
function createInsightsAndSuggestions(suggestions) {
    return `
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 my-4">
            <h4 class="font-semibold text-green-800 mb-3">🎯 발견된 패턴 & 인사이트</h4>
            <ul class="space-y-2 text-sm text-green-700 mb-4">
                ${suggestions.insights.map(insight => `<li>• ${insight}</li>`).join('')}
            </ul>
            
            <h4 class="font-semibold text-green-800 mb-3">🔍 추가 분석 제안</h4>
            <div class="space-y-2">
                ${suggestions.recommendations.map(rec => `
                    <div class="bg-white border border-green-200 rounded p-3">
                        <div class="font-medium text-green-800">${rec.title}</div>
                        <div class="text-sm text-green-600">${rec.description}</div>
                        <button class="mt-2 text-xs bg-green-100 hover:bg-green-200 px-2 py-1 rounded transition-colors" 
                                onclick="setQuestion('${rec.query}')">
                            📊 이 분석 실행하기
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 분석 제안 생성
function generateAnalysisSuggestions(analysis, originalQuestion) {
    const insights = [];
    const recommendations = [];
    
    // 인사이트 생성
    Object.entries(analysis.columnAnalysis).forEach(([col, stats]) => {
        if (stats.type === 'string' && stats.topValues.length > 0) {
            const top = stats.topValues[0];
            if (top.percentage > 40) {
                insights.push(`${col}에서 '${top.value}'가 ${top.percentage}%로 주요 패턴을 보입니다`);
            }
        }
    });
    
    // 일반적인 GA4 분석 제안
    if (originalQuestion.includes('이벤트') || analysis.columns.includes('event_name')) {
        recommendations.push({
            title: "시간대별 이벤트 분포 분석",
            description: "이벤트 발생 시간 패턴을 파악하여 최적 타이밍을 찾아보세요",
            query: "시간대별 이벤트 수를 보여주세요"
        });
        
        recommendations.push({
            title: "사용자 행동 경로 분석", 
            description: "사용자가 어떤 순서로 이벤트를 발생시키는지 분석해보세요",
            query: "사용자별 이벤트 시퀀스를 분석해주세요"
        });
    }
    
    if (analysis.columns.includes('device') || analysis.columns.some(col => col.includes('device'))) {
        recommendations.push({
            title: "디바이스별 상세 분석",
            description: "모바일/데스크톱/태블릿별 사용 패턴을 비교 분석해보세요", 
            query: "디바이스별 사용자 행동 패턴을 분석해주세요"
        });
    }
    
    if (analysis.columns.includes('geo') || analysis.columns.some(col => col.includes('country'))) {
        recommendations.push({
            title: "지역별 성과 분석",
            description: "국가/지역별 전환율과 참여도를 비교해보세요",
            query: "국가별 전환율을 분석해주세요"
        });
    }
    
    return { insights, recommendations };
}

// 창의적 HTML 분석 실행 (기존 유지)
async function executeCreativeAnalysis(question) {
    const messageId = addAssistantMessage('', true);
    
    try {
        updateMessage(messageId, '창의적 HTML 리포트를 생성하고 있습니다...');
        
        const response = await fetch('/creative-html', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            updateMessage(messageId, `
                ✅ 창의적 HTML 리포트가 생성되었습니다.
                <div class="flex gap-2 my-4">
                    <button onclick="openHtmlInNewWindow()" class="analysis-btn">🔗 새 창에서 열기</button>
                    <button onclick="downloadHtmlReport()" class="analysis-btn">💾 다운로드</button>
                </div>
                <div class="border border-gray-200 rounded-lg overflow-hidden my-4">
                    <iframe style="width: 100%; height: 400px; border: none;" sandbox="allow-scripts allow-same-origin"></iframe>
                </div>
            `);
            
            const iframe = document.querySelector(`#${messageId} iframe`);
            if (iframe) {
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                doc.open();
                doc.write(data.html_content);
                doc.close();
            }
            
            window.currentHtmlReport = data.html_content;
            window.currentQuestion = question;
            
        } else {
            updateMessage(messageId, `❌ 생성 오류: ${data.error || 'HTML 리포트 생성에 실패했습니다.'}`);
        }
        
    } catch (error) {
        updateMessage(messageId, `❌ 네트워크 오류: ${error.message}`);
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