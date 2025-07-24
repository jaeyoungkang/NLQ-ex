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
            `);
            
        } else {
            updateMessage(messageId, `❌ 오류가 발생했습니다: ${data.error || '쿼리 생성에 실패했습니다.'}`);
        }
        
    } catch (error) {
        updateMessage(messageId, `❌ 네트워크 오류: ${error.message}`);
    }
}

// 구조화 분석 실행
async function executeStructuredAnalysis(question) {
    const messageId = addAssistantMessage('', true);
    
    try {
        updateMessage(messageId, '구조화 분석을 수행하고 있습니다...');
        
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            updateMessage(messageId, `
                ✅ 구조화 분석이 완료되었습니다.
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 my-4">
                    <h4 class="font-semibold text-green-800 mb-3">📊 AI 분석 리포트</h4>
                    <div class="text-sm leading-relaxed">${parseMarkdown(data.analysis_report)}</div>
                </div>
                <div class="mt-4">${createTable(data.data)}</div>
            `);
        } else {
            updateMessage(messageId, `❌ 분석 오류: ${data.error || '구조화 분석에 실패했습니다.'}`);
        }
        
    } catch (error) {
        updateMessage(messageId, `❌ 네트워크 오류: ${error.message}`);
    }
}

// 창의적 HTML 분석 실행
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