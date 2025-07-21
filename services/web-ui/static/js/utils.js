const Utils = {
    // HTML 이스케이프
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },

    // 마크다운 파싱 (간단한 버전)
    parseMarkdown(text) {
        if (!text) return '';
        
        return text
            .replace(/### (.*$)/gim, '<h3 class="text-lg font-semibold mt-6 mb-3 text-gray-800">$1</h3>')
            .replace(/## (.*$)/gim, '<h2 class="text-xl font-semibold mt-8 mb-4 text-gray-800">$1</h2>')
            .replace(/# (.*$)/gim, '<h1 class="text-2xl font-bold mt-8 mb-6 text-gray-900">$1</h1>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold text-gray-900">$1</strong>')
            .replace(/\*(.*?)\*/gim, '<em class="italic">$1</em>')
            .replace(/`(.*?)`/gim, '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>')
            .replace(/^\- (.*$)/gim, '<li class="ml-4">$1</li>')
            .replace(/^\d+\. (.*$)/gim, '<li class="ml-4">$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul class="list-disc list-inside space-y-1 mb-4">$1</ul>')
            .replace(/\n\n/gim, '</p><p class="mb-4">')
            .replace(/^(?!<[h|u|l])/gim, '<p class="mb-4">')
            .replace(/(?<![h|u|l]>)$/gim, '</p>');
    },

    // 파일 다운로드
    downloadFile(content, mimeType, filename) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    // 날짜 포맷팅
    formatDate(dateString) {
        try {
            return new Date(dateString).toLocaleDateString('ko-KR');
        } catch (e) {
            return dateString;
        }
    },

    // 숫자 포맷팅
    formatNumber(num) {
        if (typeof num !== 'number') return num;
        return num.toLocaleString();
    },

    // 문자열 자르기
    truncateString(str, maxLength = 50) {
        if (!str || str.length <= maxLength) return str;
        return str.substring(0, maxLength) + '...';
    },

    // 디바운스 함수
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 스로틀 함수
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // 로컬 스토리지 헬퍼
    storage: {
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.warn('로컬 스토리지 저장 실패:', e);
                return false;
            }
        },

        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.warn('로컬 스토리지 읽기 실패:', e);
                return defaultValue;
            }
        },

        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.warn('로컬 스토리지 삭제 실패:', e);
                return false;
            }
        }
    }
};