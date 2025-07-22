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
            <div class="result-count">${data.row_count.toLocaleString()}개 결과</div>
        </div>

        ${tabsHtml}

        <div class="tab-content active" id="tab-data">
            <div class="table-container">
                ${createTableWithPagination(data.data)}
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
                    <code>${escapeHtml(data.generated_sql)}</code>
                </div>
            </div>
        </div>

        <div class="tab-content" id="tab-analysis">
            ${data.data_summary ? createDataSummary(data.data_summary, data.row_count) : ''}
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
            <p>총 ${data.row_count.toLocaleString()}개의 결과를 성공적으로 분석했습니다.</p>
            <p>🤖 AI 분석 리포트와 차트를 "AI 분석" 탭에서 확인하세요.</p>
        </div>
    `;

    document.getElementById('resultsSection').innerHTML = resultHtml;
    
    // 차트 생성
    if (data.chart_config) {
        setTimeout(() => createChart(data.data, data.chart_config), 100);
    }
}

// 데이터 요약 섹션 생성
function createDataSummary(dataSummary, rowCount) {
    const overview = dataSummary.overview || {};
    const insights = dataSummary.quick_insights || [];
    
    return `
        <div class="data-summary">
            <h3>📊 데이터 개요</h3>
            <div class="summary-grid">
                <div class="summary-card">
                    <h4>총 레코드</h4>
                    <div class="value">${(overview.total_rows || rowCount).toLocaleString()}</div>
                    <div class="label">개</div>
                </div>
                <div class="summary-card">
                    <h4>컬럼 수</h4>
                    <div class="value">${overview.columns_count || 0}</div>
                    <div class="label">개</div>
                </div>
                <div class="summary-card">
                    <h4>숫자형 컬럼</h4>
                    <div class="value">${Object.values(overview.data_types || {}).filter(type => type === 'numeric').length}</div>
                    <div class="label">개</div>
                </div>
                <div class="summary-card">
                    <h4>카테고리형 컬럼</h4>
                    <div class="value">${Object.values(overview.data_types || {}).filter(type => type === 'categorical').length}</div>
                    <div class="label">개</div>
                </div>
            </div>
            ${insights && insights.length > 0 ? `
            <div class="insights-section" style="margin-top: 1.5rem;">
                <h4>🎯 핵심 인사이트</h4>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                    ${insights.map(insight => `<li style="margin-bottom: 0.5rem;">${insight}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
    `;
}

// 페이지네이션이 포함된 테이블 생성
function createTableWithPagination(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">조회된 데이터가 없습니다.</div>';
    }

    const pageSize = 25;
    const totalPages = Math.ceil(data.length / pageSize);
    
    if (totalPages === 1) {
        return createTable(data);
    }

    // 첫 페이지 데이터만 표시
    const firstPageData = data.slice(0, pageSize);
    
    return `
        ${createTable(firstPageData)}
        <div class="table-pagination" style="margin-top: 1rem; text-align: center; padding: 1rem; background: #f9fafb; border-radius: 0.5rem;">
            <div class="pagination-info" style="margin-bottom: 1rem; color: #6b7280;">
                <span>페이지 1 / ${totalPages} (총 ${data.length.toLocaleString()}개 결과)</span>
            </div>
            <div class="pagination-controls">
                <button onclick="showTablePage(1)" class="pagination-btn active" data-page="1">1</button>
                ${totalPages > 1 ? `<button onclick="showTablePage(2)" class="pagination-btn" data-page="2">2</button>` : ''}
                ${totalPages > 2 ? `<button onclick="showTablePage(3)" class="pagination-btn" data-page="3">3</button>` : ''}
                ${totalPages > 3 ? '<span class="pagination-dots">...</span>' : ''}
                ${totalPages > 3 ? `<button onclick="showTablePage(${totalPages})" class="pagination-btn" data-page="${totalPages}">${totalPages}</button>` : ''}
            </div>
            <style>
                .pagination-btn {
                    padding: 0.5rem 0.75rem;
                    margin: 0 0.25rem;
                    border: 1px solid #d1d5db;
                    background: white;
                    color: #374151;
                    border-radius: 0.375rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .pagination-btn:hover {
                    background: #f3f4f6;
                }
                .pagination-btn.active {
                    background: #3b82f6;
                    color: white;
                    border-color: #3b82f6;
                }
                .pagination-dots {
                    padding: 0.5rem;
                    color: #6b7280;
                }
            </style>
        </div>
    `;
}

// 테이블 페이지 전환
function showTablePage(pageNumber) {
    // 이 함수는 실제로는 모든 데이터를 다시 렌더링해야 하므로
    // 현재는 간단한 알림만 표시
    alert(`페이지 ${pageNumber}로 이동하는 기능은 구현 예정입니다. 전체 데이터를 보려면 "창의적 HTML" 모드를 사용하세요.`);
}

// 탭 전환 함수
function showTab(tabName) {
    // 모든 탭 버튼과 콘텐츠의 active 클래스 제거
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // 클릭된 탭 버튼과 해당 콘텐츠에 active 클래스 추가
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // 분석 탭으로 전환 시 차트 리사이즈
    if (tabName === 'analysis' && currentChart) {
        setTimeout(() => {
            currentChart.resize();
            currentChart.update();
        }, 100);
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
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                cornerRadius: 8,
                displayColors: true
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
                    'rgba(121, 85, 72, 0.8)',
                    'rgba(96, 125, 139, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(139, 195, 74, 0.8)',
                    'rgba(255, 87, 34, 0.8)',
                    'rgba(63, 81, 181, 0.8)',
                    'rgba(158, 158, 158, 0.8)',
                    'rgba(205, 220, 57, 0.8)',
                    'rgba(255, 235, 59, 0.8)',
                    'rgba(67, 160, 71, 0.8)',
                    'rgba(244, 67, 54, 0.8)'
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
                    'rgba(121, 85, 72, 1)',
                    'rgba(96, 125, 139, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(139, 195, 74, 1)',
                    'rgba(255, 87, 34, 1)',
                    'rgba(63, 81, 181, 1)',
                    'rgba(158, 158, 158, 1)',
                    'rgba(205, 220, 57, 1)',
                    'rgba(255, 235, 59, 1)',
                    'rgba(67, 160, 71, 1)',
                    'rgba(244, 67, 54, 1)'
                ],
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
                },
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString();
                    }
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    maxRotation: 45,
                    minRotation: 0
                }
            }
        };
        
    } else if (config.type === 'line' && config.label_column && config.value_columns) {
        // 선 차트 (다중 데이터)
        const labels = data.slice(0, 50).map(row => String(row[config.label_column])); // 상위 50개
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
                data: data.slice(0, 50).map(row => Number(row[col]) || 0),
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length].replace('1)', '0.1)'),
                tension: 0.4,
                fill: false,
                pointBackgroundColor: colors[index % colors.length],
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            };
        });
        
        chartData = { labels, datasets };
        
        chartOptions.scales = {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString();
                    }
                }
            },
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        };
    }
    
    // 차트 생성
    try {
        currentChart = new Chart(ctx, {
            type: config.type,
            data: chartData,
            options: chartOptions
        });
    } catch (error) {
        console.error('차트 생성 오류:', error);
        document.getElementById('analysisChart').style.display = 'none';
        document.querySelector('.chart-container').innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #6b7280;">
                📊 차트를 생성할 수 없습니다. 데이터 형식을 확인해주세요.
            </div>
        `;
    }
}

// 마크다운 파싱 (개선된 버전)
function parseMarkdown(text) {
    if (!text) return '';
    
    return text
        // 헤딩 처리
        .replace(/### (.*$)/gim, '<h3>$1</h3>')
        .replace(/## (.*$)/gim, '<h2>$1</h2>')
        .replace(/# (.*$)/gim, '<h1>$1</h1>')
        
        // 텍스트 포맷팅
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/`(.*?)`/gim, '<code>$1</code>')
        
        // 리스트 처리 (개선)
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
        
        // 연속된 li 태그들을 ul로 감싸기
        .replace(/(<li>.*<\/li>)/s, function(match) {
            const listItems = match.match(/<li>.*?<\/li>/g);
            if (listItems && listItems.length > 1) {
                return '<ul>' + listItems.join('') + '</ul>';
            }
            return '<ul>' + match + '</ul>';
        })
        
        // 단락 처리
        .replace(/\n\n/gim, '</p><p>')
        .replace(/^(?!<[h|u|o|l])/gim, '<p>')
        .replace(/(?<![>])$/gim, '</p>')
        
        // 정리
        .replace(/<p><\/p>/gim, '')
        .replace(/<p>(<[h|u|o])/gim, '$1')
        .replace(/(<\/[h|u|o]>)<\/p>/gim, '$1');
}

// 테이블 생성 함수 (analysis.js용 - 개선된 버전)
function createTable(data) {
    if (!data || data.length === 0) {
        return '<div class="no-data">조회된 데이터가 없습니다.</div>';
    }

    // 헤더 생성
    const headers = Object.keys(data[0]);
    const headerHtml = headers.map(header => 
        `<th>${escapeHtml(header)}</th>`
    ).join('');

    // 행 생성 (최대 100개까지 표시)
    const displayData = data.slice(0, 100);
    const rowsHtml = displayData.map((row, index) => {
        const cellsHtml = headers.map(header => {
            const value = row[header];
            return `<td>${formatCellValue(value)}</td>`;
        }).join('');
        return `<tr>${cellsHtml}</tr>`;
    }).join('');

    const hasMoreData = data.length > 100;
    const tableFooter = hasMoreData ? 
        `<div class="table-footer" style="text-align: center; padding: 1rem; background: #f9fafb; color: #6b7280; border-radius: 0 0 0.75rem 0.75rem;">
            📊 ${data.length.toLocaleString()}개 중 ${displayData.length}개만 표시됩니다. 
            전체 결과를 보려면 <strong>"창의적 HTML"</strong> 모드를 사용하세요.
        </div>` : '';

    return `
        <table>
            <thead>
                <tr>${headerHtml}</tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
        ${tableFooter}
    `;
}

// 셀 값 포맷팅 (개선된 버전)
function formatCellValue(value) {
    if (value === null || value === undefined) {
        return '<em style="color: #999; font-style: italic;">NULL</em>';
    }
    
    if (typeof value === 'number') {
        // 큰 수는 천 단위 구분자 추가
        if (Math.abs(value) >= 1000) {
            return value.toLocaleString();
        }
        // 소수점이 있는 경우 적절히 반올림
        if (value % 1 !== 0) {
            return parseFloat(value.toFixed(4)).toString();
        }
        return value.toString();
    }
    
    if (typeof value === 'string') {
        // 날짜 형식 감지 및 포맷팅
        if (value.match(/^\d{4}-\d{2}-\d{2}/)) {
            try {
                const date = new Date(value);
                return date.toLocaleDateString('ko-KR');
            } catch (e) {
                return escapeHtml(value);
            }
        }
        
        // URL 감지 및 링크 생성
        if (value.match(/^https?:\/\//)) {
            return `<a href="${escapeHtml(value)}" target="_blank" style="color: #3b82f6; text-decoration: underline;">${escapeHtml(value.substring(0, 50))}${value.length > 50 ? '...' : ''}</a>`;
        }
        
        // 긴 텍스트는 잘라서 표시
        if (value.length > 80) {
            return `<span title="${escapeHtml(value)}" style="cursor: help;">${escapeHtml(value.substring(0, 80))}...</span>`;
        }
    }
    
    return escapeHtml(String(value));
}

// HTML 이스케이프 (analysis.js용)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}