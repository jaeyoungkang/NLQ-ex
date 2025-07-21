const Examples = {
    categories: {
        basic: {
            title: '🔢 기본 분석',
            color: 'text-google-blue',
            questions: [
                '총 이벤트 수를 알려주세요',
                '가장 많이 발생한 이벤트 유형 상위 10개',
                '고유 사용자 수를 알려주세요',
                '세션 수를 알려주세요'
            ]
        },
        
        geographic: {
            title: '🌍 지역별 분석',
            color: 'text-google-green',
            questions: [
                '국가별 사용자 수를 보여주세요',
                '한국 사용자들의 이벤트 수를 알려주세요',
                '도시별 이벤트 수 상위 10개',
                '미국과 한국 사용자 비교'
            ]
        },
        
        device: {
            title: '📱 기기 및 플랫폼',
            color: 'text-google-yellow',
            questions: [
                '모바일과 데스크톱 사용자 비율을 알려주세요',
                '운영체제별 사용자 분포를 보여주세요',
                '플랫폼별 이벤트 수를 보여주세요',
                '브라우저별 사용자 현황'
            ]
        },
        
        temporal: {
            title: '🕐 시간대별 분석',
            color: 'text-google-red',
            questions: [
                '시간대별 이벤트 수를 보여주세요',
                'page_view 이벤트가 가장 많은 시간대',
                '요일별 사용자 활동 패턴'
            ]
        },
        
        ecommerce: {
            title: '🛒 전자상거래',
            color: 'text-google-purple',
            questions: [
                'purchase 이벤트의 총 매출을 보여주세요',
                'add_to_cart 이벤트가 많은 상위 10개 사용자',
                '구매 전환율 분석',
                '장바구니 포기율 계산'
            ]
        },
        
        traffic: {
            title: '🔗 트래픽 소스',
            color: 'text-google-orange',
            questions: [
                '트래픽 소스별 이벤트 수를 보여주세요',
                '유료 광고 vs 자연 검색 비교',
                '추천 사이트별 유입 현황'
            ]
        }
    },

    // 모든 카테고리 렌더링
    renderAll() {
        return Object.entries(this.categories).map(([key, category]) => 
            this.renderCategory(category)
        ).join('');
    },

    // 개별 카테고리 렌더링
    renderCategory(category) {
        return `
            <div class="mb-6">
                <h4 class="text-md font-medium ${category.color} mb-3">${category.title}</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    ${category.questions.map(question => this.renderQuestionItem(question)).join('')}
                </div>
            </div>
        `;
    },

    // 개별 질문 아이템 렌더링
    renderQuestionItem(question) {
        return `
            <div class="example-item p-3 border border-gray-200 rounded-lg cursor-pointer example-hover transition-all duration-150" onclick="setQuestion('${question}')">
                <code class="text-sm text-google-blue">"${question}"</code>
            </div>
        `;
    },

    // 랜덤 질문 가져오기
    getRandomQuestion() {
        const allQuestions = Object.values(this.categories)
            .flatMap(category => category.questions);
        
        return allQuestions[Math.floor(Math.random() * allQuestions.length)];
    },

    // 카테고리별 질문 가져오기
    getQuestionsByCategory(categoryKey) {
        return this.categories[categoryKey]?.questions || [];
    },

    // 검색 기능
    searchQuestions(keyword) {
        const allQuestions = Object.values(this.categories)
            .flatMap(category => category.questions);
        
        return allQuestions.filter(question => 
            question.toLowerCase().includes(keyword.toLowerCase())
        );
    }
};