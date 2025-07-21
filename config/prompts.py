# config/prompts.py
"""
AI 프롬프트 설정 모음
"""

from .schema_config import PROJECT_ID, get_schema_prompt

def get_sql_generation_system_prompt():
    """SQL 생성을 위한 시스템 프롬프트"""
    schema_prompt = get_schema_prompt()
    
    return f"""당신은 BigQuery SQL 전문가이며, GA4 (Google Analytics 4) 데이터 분석에 특화되어 있습니다. 
사용자의 자연어 질문을 BigQuery SQL 쿼리로 변환해주세요.

{schema_prompt}

중요한 규칙:
1. BigQuery 표준 SQL 문법을 사용해주세요.
2. 테이블 참조 시 반드시 백틱(`)을 사용하여 `{PROJECT_ID}.test_dataset.events_20201121` 형식으로 사용하세요.
3. GA4의 중첩된 구조체 접근 시 올바른 문법을 사용하세요 (예: device.category, geo.country).
4. event_params 배열에서 값을 추출할 때는 UNNEST와 서브쿼리를 사용하세요.
5. 타임스탬프 변환 시 TIMESTAMP_MICROS() 함수를 사용하세요.
6. SQL 쿼리만 반환하고, 다른 설명은 포함하지 마세요.
7. 쿼리는 반드시 세미콜론(;)으로 끝나야 합니다.
8. 결과 수를 제한할 필요가 있다면 LIMIT 절을 사용하세요.

GA4 일반적인 쿼리 패턴:
- 이벤트 수 집계: SELECT event_name, COUNT(*) as event_count FROM table GROUP BY event_name
- 기기별 분석: SELECT device.category, COUNT(*) as count FROM table GROUP BY device.category
- 지역별 분석: SELECT geo.country, COUNT(DISTINCT user_pseudo_id) as users FROM table GROUP BY geo.country
- 시간대별 분석: SELECT EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp)) as hour, COUNT(*) FROM table GROUP BY hour
- 구매 분석: SELECT SUM(ecommerce.purchase_revenue_in_usd) as total_revenue FROM table WHERE event_name = 'purchase'

예시:
질문: "오늘 총 이벤트 수를 알려주세요"
답변: SELECT COUNT(*) as total_events FROM `{PROJECT_ID}.test_dataset.events_20201121`;

질문: "가장 많이 발생한 이벤트 유형 상위 5개를 보여주세요"
답변: SELECT event_name, COUNT(*) as event_count FROM `{PROJECT_ID}.test_dataset.events_20201121` GROUP BY event_name ORDER BY event_count DESC LIMIT 5;

질문: "국가별 고유 사용자 수를 보여주세요"
답변: SELECT geo.country, COUNT(DISTINCT user_pseudo_id) as unique_users FROM `{PROJECT_ID}.test_dataset.events_20201121` GROUP BY geo.country ORDER BY unique_users DESC;"""

def get_analysis_report_prompt(question, sql_query, data_analysis, summary_insights, query_results, max_rows_for_analysis=100):
    """분석 리포트 생성을 위한 프롬프트"""
    import json
    
    # 샘플링
    sample_data = query_results[:max_rows_for_analysis] if len(query_results) > max_rows_for_analysis else query_results
    
    return f"""다음은 GA4 데이터 분석 결과입니다. Claude Console과 같은 스타일로 구조화된 분석 리포트를 작성해주세요.

**원본 질문:** {question}

**데이터 개요:**
- 총 레코드 수: {data_analysis['row_count']:,}개
- 컬럼 수: {len(sample_data[0].keys()) if sample_data else 0}개
- 컬럼 구성: {', '.join([f"{col}({stats['type']})" for col, stats in data_analysis['columns'].items()])}

**핵심 통계:**
{json.dumps(data_analysis['columns'], indent=2, ensure_ascii=False, default=str)}

**자동 생성된 인사이트:**
{chr(10).join(summary_insights)}

**샘플 데이터 (상위 5개 행):**
{json.dumps(query_results[:5], indent=2, ensure_ascii=False, default=str)}

다음과 같은 Claude Console 스타일로 리포트를 작성해주세요:

## 📊 데이터 분석 리포트

### 🎯 핵심 인사이트
(3-4개의 핵심 발견사항을 간결하고 명확하게 제시)

### 📈 주요 통계
(숫자로 표현 가능한 핵심 지표들)

### 🔍 패턴 분석
(데이터에서 발견되는 트렌드나 패턴)

### 💡 비즈니스 시사점
(실무진이 활용할 수 있는 구체적인 제안)

### 🚀 다음 단계 제안
(추가 분석이나 액션 아이템)

**작성 지침:**
- 각 섹션은 간결하고 스캔 가능하도록 작성
- 구체적인 수치와 퍼센티지 포함
- 이모지를 활용한 시각적 구분
- 업무에 바로 적용 가능한 내용 위주
- 차트가 있다면 차트 해석 포함"""

def get_html_generation_prompt(question, sql_query, query_results):
    """HTML 생성을 위한 프롬프트"""
    import json
    from ..utils.data_utils import safe_json_serialize
    
    # 안전한 데이터 타입 검증
    try:
        if not query_results:
            query_results = []
        elif not isinstance(query_results, list):
            query_results = []
        
        if query_results and not isinstance(query_results[0], dict):
            query_results = []
        
        # 데이터 준비 (안전하게)
        sample_data = query_results[:10] if len(query_results) > 10 else query_results
        columns = list(sample_data[0].keys()) if sample_data and isinstance(sample_data[0], dict) else []
        
        # Chart.js용 데이터 변환 (안전하게)
        chart_data = []
        chart_labels = []
        
        if len(columns) >= 2 and sample_data:
            try:
                for row in sample_data:
                    if isinstance(row, dict) and columns[0] in row:
                        # 라벨 처리
                        label_value = row[columns[0]]
                        chart_labels.append(str(label_value) if label_value is not None else "")
                        
                        # 값 처리
                        if len(columns) >= 2 and columns[1] in row:
                            value = row[columns[1]]
                            if isinstance(value, (int, float)):
                                chart_data.append(value)
                            else:
                                try:
                                    chart_data.append(float(value))
                                except (ValueError, TypeError):
                                    chart_data.append(0)
                        else:
                            chart_data.append(0)
            except Exception as e:
                chart_data = []
                chart_labels = []
        
        # 안전한 JSON 직렬화를 위한 데이터 정리
        safe_sample_data = safe_json_serialize(sample_data[:3])
        safe_chart_labels = safe_json_serialize(chart_labels[:5])
        safe_chart_data = safe_json_serialize(chart_data[:5])
        
    except Exception as e:
        safe_sample_data = []
        safe_chart_labels = []
        safe_chart_data = []
    
    return f"""다음 GA4 데이터 분석 결과를 완전한 HTML 페이지로 생성해주세요.

**원본 질문:** {question}

**실행된 SQL:**
```sql
{sql_query}
```

**데이터 정보:**
- 총 행 수: {len(query_results)}개
- 컬럼: {', '.join(columns) if columns else '없음'}

**샘플 데이터 (상위 3개):**
{json.dumps(safe_sample_data, indent=2, ensure_ascii=False)}

**차트 데이터:**
- Labels: {safe_chart_labels}
- Data: {safe_chart_data}

다음 요구사항에 맞는 완전한 HTML을 생성해주세요:

1. **완전히 독립적인 HTML 파일** (DOCTYPE부터 </html>까지)
2. **Chart.js 차트 포함** (CDN: https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js)
3. **Google 브랜드 컬러** (#4285f4, #34a853 등)
4. **반응형 디자인** (모바일 대응)
5. **구조화된 분석 리포트** (핵심 인사이트, 통계, 비즈니스 시사점)

HTML 구조:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{question} - GA4 분석 리포트</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        /* 필요한 모든 CSS 스타일 */
    </style>
</head>
<body>
    <!-- 완전한 HTML 콘텐츠 -->
    <script>
        // Chart.js 구현
    </script>
</body>
</html>
```

중요 사항:
- 실제 데이터 값을 활용한 구체적인 인사이트 제공
- 작동하는 Chart.js 코드 포함
- 모든 스타일을 인라인으로 포함
- 한국어로 자연스러운 분석 내용 작성
- 비즈니스 관점의 실용적인 제안사항 포함

완전한 HTML 코드만 반환해주세요."""