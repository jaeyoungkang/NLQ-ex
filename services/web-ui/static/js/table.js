const TableManager = {
    createTable(data) {
        if (!data || data.length === 0) {
            return this.createEmptyState();
        }

        const headers = Object.keys(data[0]);
        const displayData = data.slice(0, 100); // 성능을 위해 100개만
        
        return `
            <div class="border border-gray-200 rounded-lg overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="min-w-full">
                        <thead>${this.createHeaders(headers)}</thead>
                        <tbody>${this.createRows(displayData, headers)}</tbody>
                    </table>
                </div>
                ${this.createPaginationInfo(data.length, displayData.length)}
            </div>
        `;
    },

    createHeaders(headers) {
        return `<tr>${headers.map(h => 
            `<th class="px-4 py-3 bg-google-blue text-white text-left text-sm font-medium uppercase">${Utils.escapeHtml(h)}</th>`
        ).join('')}</tr>`;
    },

    createRows(data, headers) {
        return data.map(row => 
            `<tr class="hover:bg-gray-50">${headers.map(h => 
                `<td class="px-4 py-3 text-sm text-gray-700 border-b border-gray-200">${this.formatCell(row[h])}</td>`
            ).join('')}</tr>`
        ).join('');
    },

    createPaginationInfo(total, displayed) {
        if (total <= displayed) return '';
        
        return `
            <div class="bg-blue-50 border-t border-blue-200 px-4 py-3 text-sm text-blue-700">
                <span class="font-medium">알림:</span> 성능을 위해 상위 ${displayed}개 결과만 표시됩니다. 
                전체 ${total.toLocaleString()}개 중 ${displayed}개
            </div>
        `;
    },

    createEmptyState() {
        return `
            <div class="text-center py-12">
                <div class="text-gray-400 text-6xl mb-4">📊</div>
                <h3 class="text-lg font-medium text-gray-700 mb-2">조회된 데이터가 없습니다</h3>
                <p class="text-gray-500">다른 질문을 시도해보세요.</p>
            </div>
        `;
    },

    formatCell(value) {
        if (value === null || value === undefined) {
            return '<span class="text-gray-400 italic">NULL</span>';
        }
        if (typeof value === 'number') {
            return `<span class="font-mono">${value.toLocaleString()}</span>`;
        }
        if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
            try {
                return `<span class="text-blue-600">${new Date(value).toLocaleDateString('ko-KR')}</span>`;
            } catch (e) {
                return Utils.escapeHtml(value);
            }
        }
        if (typeof value === 'string' && value.length > 50) {
            return `<span title="${Utils.escapeHtml(value)}">${Utils.escapeHtml(value.substring(0, 50))}...</span>`;
        }
        return Utils.escapeHtml(String(value));
    }
};