// static/js/analysis.js
// 구조화된 분석 결과 처리 및 차트 생성 관련 JavaScript

// 전역 변수
let currentChart = null;

// 구조화된 분석 결과 표시
function displayStructuredResults(data) {
    let tabsHtml = `
        <div class="results-tabs">
            <button class="tab-button active" onclick="showTab('data')">📊 데이터</button>
            <button class="tab-button" onclick="showTab('query')">📝 쿼리 정보</button>
            <button class="tab-button" onclick="showTab('analysis')">🤖 AI 분석</button>
        </div>
    `;

    let resultHtml = `
        <div class="results-header">
            <h2>📊 구조화 분석 결과 <span class="mode-badge structured">STRUCTURED</span></h2>
            <div class="result-count">${data.row_count}개 결과</div>
        </div>

        ${tabsHtml}

        <div class="tab-content active" id="tab-data">
            <div class="table-container">
                ${createTable(data.data)}
            </div>
        </div>

        <div class="tab-content" id="tab-query">
            <div class="query-info">
                <h3>📝 질문 정보</h3>
                <div class="original-question">
                    <strong>원본 질문:</strong> ${escapeHtml(data.original_question)}
                </div>
                <div class="generated-sql">
                    <strong>생성된 SQL:</strong><br>
                    ${escapeHtml(data.generated_sql)}
                </div>
            </div>
        </div>

        <div class="tab-content" id="tab-analysis">
            ${data.data_summary ? `
            <div class="data-summary">
                <h3>📊 데이터 개요</h3>
                <div class="summary-grid">
                    <div class="summary-card">
                        <h4>총 레코드</h4>
                        <div class="value">${data.data_summary.overview.total_rows.toLocaleString()}</div>
                        <div class="label">개</div>
                    </div>
                    <div class="summary-card">
                        <h4>컬럼 수</h4>
                        <div class="value">${data.data_summary.overview.columns_count}</div>
                        <div class="label">개</div>
                    </div>
                    <div class="summary-card">
                        <h4>데이터 타입</h4>
                        <div class="value">${Object.values(data.data_summary.overview.data_types).filter(type => type === 'numeric').length}</div>
                        <div class="label">숫자형</div>
                    </div>
                    <div class="summary-card">
                        <h4>카테고리형</h4>
                        <div class="value">${Object.values(data.data_summary.overview.data_types).filter(type => type === 'categorical').length}</div>
                        <div class="label">개</div>
                    </div>
                </div>
                ${data.data_summary.quick_insights && data.data_summary.quick_insights.length > 0 ? `
                <div class="insights-list">
                    <h4>🎯 빠른 인사이트</h4>
                    <ul>
                        ${data.data_summary.quick_insights.map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
            ` : ''}
            ${data.chart_config ? `
            <div class="chart-container">
                <h4>${data.chart_config.title || '데이터 시각화'}</h4>
                <div class="chart-wrapper">
                    <canvas id="analysisChart"></canvas>
                </div>
            </div>
            ` : ''}
            <div class="analysis-report">
                ${parseMarkdown(data.analysis_report)}
            </div>
        </div>

        <div class="success">
            <h3>✅ 분석 완료</h3>
            <p>총 ${data.row_count}개의 결과를 성공적으로 분석했습니다.</p>
            <p>🤖 AI 분석 리포트와 차트를 "AI 분석" 탭에서 확인하세요.</p>
        </div>
    `;

    document.getElementById('resultsSection').innerHTML = resultHtml;
    
    // 차트 생성
    if (data.chart_config) {
        setTimeout(() => createChart(data.data, data.chart_config), 100);
    }
}

// 탭 전환 함수
function showTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    if (tabName === 'analysis' && currentChart) {
        setTimeout(() => currentChart.resize(), 100);
    }
}

// 차트 생성 함수
function createChart(data, config) {
    const canvas = document.getElementById('analysisChart');
    if (!canvas || !data || data.length === 0) return;
    
    // 기존 차트 제거
    if (currentChart) {
        currentChart.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    
    let chartData = {};
    let chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: config.title || '데이터 시각화'
            }
        }
    };
    
    if (config.type === 'bar' && config.label_column && config.value_column) {
        // 막대 차트
        const labels = data.map(row => String(row[config.label_column]));
        const values = data.map(row => Number(row[config.value_column]) || 0);
        
        chartData = {
            labels: labels,
            datasets: [{
                label: config.value_column,
                data: values,
                backgroundColor: [
                    'rgba(66, 133, 244, 0.8)',
                    'rgba(52, 168, 83, 0.8)',
                    'rgba(251, 188, 5, 0.8)',
                    'rgba(234, 67, 53, 0.8)',
                    'rgba(156, 39, 176, 0.8)',
                    'rgba(255, 152, 0, 0.8)',
                    'rgba(0, 172, 193, 0.8)',
                    'rgba(76, 175, 80, 0.8)',
                    'rgba(233, 30, 99, 0.8)',
                    'rgba(121, 85, 72, 0.8)'
                ],
                borderColor: [
                    'rgba(66, 133, 244, 1)',
                    'rgba(52, 168, 83, 1)',
                    'rgba(251, 188, 5, 1)',
                    'rgba(234, 67, 53, 1)',
                    'rgba(156, 39, 176, 1)',
                    'rgba(255, 152, 0, 1)',
                    'rgba(0, 172, 193, 1)',
                    'rgba(76, 175, 80, 1)',
                    'rgba(233, 30, 99, 1)',
                    'rgba(121, 85, 72, 1)'
                ],
                borderWidth: 1
            }]
        };
        
        chartOptions.scales = {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString();
                    }
                }
            }
        };
        
    } else if (config.type === 'line' && config.label_column && config.value_columns) {
        // 선 차트 (다중 데이터)
        const labels = data.map(row => String(row[config.label_column]));
        const datasets = config.value_columns.map((col, index) => {
            const colors = [
                'rgba(66, 133, 244, 1)',
                'rgba(52, 168, 83, 1)',
                'rgba(251, 188, 5, 1)',
                'rgba(234, 67, 53, 1)',
                'rgba(156, 39, 176, 1)'
            ];
            
            return {
                label: col,
                data: data.map(row => Number(row[col]) || 0),
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length].replace('1)', '0.2)'),
                tension: 0.1,
                fill: false
            };
        });
        
        chartData = { labels, datasets };
        
        chartOptions.scales = {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString();
                    }
                }
            }
        };
    }
    
    // 차트 생성
    currentChart = new Chart(ctx, {
        type: config.type,
        data: chartData,
        options: chartOptions
    });
}

// 마크다운 파싱 (간단한 버전)
function parseMarkdown(text) {
    return text
        .replace(/### (.*$)/gim, '<h3>$1</h3>')
        .replace(/## (.*$)/gim, '<h2>$1</h2>')
        .replace(/# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/`(.*?)`/gim, '<code>$1</code>')
        .replace(/^\- (.*$)/gim, '<li>$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        .replace(/\n\n/gim, '</p><p>')
        .replace(/^(?!<[h|u|l])/gim, '<p>')
        .replace(/(?<![h|u|l]>)$/gim, '</p>');
}