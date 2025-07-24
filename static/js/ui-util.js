// ui-utils.js - UI 관련 유틸리티 함수들

// 테이블 생성
function createTable(data) {
    if (!data || data.length === 0) {
        return '<div class="text-center py-8 text-gray-500">조회된 데이터가 없습니다.</div>';
    }

    const headers = Object.keys(data[0]);
    const headerHtml = headers.map(header => 
        `<th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">${escapeHtml(header)}</th>`
    ).join('');

    const displayData = data.slice(0, 50);
    const rowsHtml = displayData.map((row, index) => {
        const cellsHtml = headers.map(header => {
            const value = row[header];
            return `<td class="px-4 py-3 text-sm text-gray-900 border-b border-gray-100">${formatCellValue(value)}</td>`;
        }).join('');
        const bgClass = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
        return `<tr class="${bgClass} hover:bg-blue-50 transition-colors">${cellsHtml}</tr>`;
    }).join('');

    const hasMoreData = data.length > 50;
    const moreDataMessage = hasMoreData ? 
        `<div class="text-center py-3 text-sm text-gray-500 bg-gray-50 border-t border-gray-200">📊 ${data.length}개 중 50개만 표시됩니다.</div>` : '';

    return `
        <div class="overflow-x-auto border border-gray-200 rounded-lg">
            <table class="min-w-full">
                <thead class="bg-gray-100"><tr>${headerHtml}</tr></thead>
                <tbody>${rowsHtml}</tbody>
            </table>
            ${moreDataMessage}
        </div>
    `;
}

// 셀 값 포맷팅
function formatCellValue(value) {
    if (value === null || value === undefined) {
        return '<span class="text-gray-400 italic">NULL</span>';
    }
    
    if (typeof value === 'number') {
        return value.toLocaleString();
    }
    
    const stringValue = String(value);
    if (stringValue.length > 100) {
        return `<span title="${escapeHtml(stringValue)}" class="cursor-help">${escapeHtml(stringValue.substring(0, 100))}...</span>`;
    }
    
    return escapeHtml(stringValue);
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// sleep 함수
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 마크다운 파싱 (간단 버전)
function parseMarkdown(text) {
    if (!text) return '';
    
    return text
        .replace(/### (.*$)/gim, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
        .replace(/## (.*$)/gim, '<h2 class="text-xl font-semibold mt-4 mb-2">$1</h2>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold">$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em class="italic">$1</em>')
        .replace(/`(.*?)`/gim, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
        .replace(/^\* (.*$)/gim, '<li class="ml-4">$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul class="list-disc list-inside space-y-1 my-2">$1</ul>')
        .replace(/\n\n/gim, '</p><p class="mb-2">')
        .replace(/^(?!<)/gim, '<p class="mb-2">')
        .replace(/$/gim, '</p>');
}