const API = {
    // 기본 설정
    baseURL: '',
    
    endpoints: {
        quick: '/api/quick',
        structured: '/api/analyze',
        creative: '/api/creative-html'
    },

    // 쿼리 실행
    async executeQuery(question, mode) {
        const endpoint = this.endpoints[mode];
        if (!endpoint) {
            throw new Error(`알 수 없는 모드: ${mode}`);
        }

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || '서버 오류가 발생했습니다.');
        }

        return data;
    },

    // 헬스체크
    async healthCheck() {
        try {
            const response = await fetch('/health');
            return response.ok;
        } catch (error) {
            return false;
        }
    }
};