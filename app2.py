from flask import Flask, request, jsonify, send_from_directory
from google.cloud import bigquery
import anthropic
import os
import json
import re
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """정적 파일 서빙"""
    return send_from_directory('.', filename)

# 환경 변수에서 API 키 읽기
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("경고: ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

# Anthropic 클라이언트 초기화
try:
    anthropic_client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY
    ) if ANTHROPIC_API_KEY else None
except Exception as e:
    print(f"Anthropic 클라이언트 초기화 실패: {e}")
    anthropic_client = None

# 프로젝트 ID 명시적 설정
PROJECT_ID = "nlq-ex"

# BigQuery 클라이언트 초기화 (프로젝트 ID 명시)
try:
    bigquery_client = bigquery.Client(project=PROJECT_ID)
    print(f"BigQuery 프로젝트 ID: {PROJECT_ID}")
    print(f"BigQuery 클라이언트 프로젝트: {bigquery_client.project}")
except Exception as e:
    print(f"BigQuery 클라이언트 초기화 실패: {e}")
    bigquery_client = None

# GA4 Events 테이블 스키마 정보
TABLE_SCHEMA = {
    "events_20201121": {
        "description": "GA4 이벤트 데이터 (2020년 11월 21일)",
        "columns": [
            {"name": "event_date", "type": "STRING", "description": "이벤트 날짜 (YYYYMMDD 형식)"},
            {"name": "event_timestamp", "type": "INTEGER", "description": "이벤트 타임스탬프 (마이크로초)"},
            {"name": "event_name", "type": "STRING", "description": "이벤트 이름 (page_view, purchase, add_to_cart 등)"},
            {"name": "event_previous_timestamp", "type": "INTEGER", "description": "이전 이벤트 타임스탬프"},
            {"name": "event_value_in_usd", "type": "FLOAT", "description": "이벤트 값 (USD)"},
            {"name": "event_bundle_sequence_id", "type": "INTEGER", "description": "이벤트 번들 시퀀스 ID"},
            {"name": "event_server_timestamp_offset", "type": "INTEGER", "description": "서버 타임스탬프 오프셋"},
            {"name": "user_id", "type": "STRING", "description": "사용자 ID"},
            {"name": "user_pseudo_id", "type": "STRING", "description": "익명 사용자 ID"},
            {"name": "privacy_info", "type": "RECORD", "description": "개인정보 관련 정보"},
            {"name": "user_properties", "type": "RECORD", "description": "사용자 속성 (중첩된 키-값 쌍)"},
            {"name": "user_first_touch_timestamp", "type": "INTEGER", "description": "사용자 첫 접촉 타임스탬프"},
            {"name": "user_ltv", "type": "RECORD", "description": "사용자 생애가치 정보"},
            {"name": "device", "type": "RECORD", "description": "기기 정보 (category, mobile_brand_name, operating_system 등)"},
            {"name": "geo", "type": "RECORD", "description": "지리적 정보 (country, region, city 등)"},
            {"name": "app_info", "type": "RECORD", "description": "앱 정보 (id, version, install_store 등)"},
            {"name": "traffic_source", "type": "RECORD", "description": "트래픽 소스 정보 (name, medium, source 등)"},
            {"name": "stream_id", "type": "STRING", "description": "스트림 ID"},
            {"name": "platform", "type": "STRING", "description": "플랫폼 (WEB, IOS, ANDROID)"},
            {"name": "event_params", "type": "RECORD", "description": "이벤트 매개변수 (중첩된 키-값 쌍)"},
            {"name": "ecommerce", "type": "RECORD", "description": "전자상거래 정보 (purchase_revenue, items 등)"},
            {"name": "items", "type": "RECORD", "description": "상품 정보 배열 (item_id, item_name, price 등)"}
        ],
        "sample_queries": [
            "오늘 이벤트 수를 알려주세요",
            "가장 많이 발생한 이벤트 유형을 보여주세요",
            "국가별 사용자 수를 보여주세요",
            "모바일과 데스크톱 사용자 비율을 보여주세요",
            "purchase 이벤트의 총 매출을 보여주세요",
            "page_view 이벤트가 가장 많은 시간대를 보여주세요",
            "운영체제별 사용자 분포를 보여주세요",
            "트래픽 소스별 이벤트 수를 보여주세요"
        ]
    }
}

def get_schema_prompt():
    """GA4 테이블 스키마 정보를 프롬프트 형태로 변환"""
    full_table_name = f"`{PROJECT_ID}.test_dataset.events_20201121`"
    
    schema_text = f"""다음은 BigQuery GA4 이벤트 데이터의 테이블 스키마 정보입니다 (프로젝트: {PROJECT_ID}):

테이블: {full_table_name}
설명: Google Analytics 4 이벤트 데이터 (2020년 11월 21일)

주요 컬럼:
- event_date (STRING): 이벤트 날짜 (YYYYMMDD 형식)
- event_timestamp (INTEGER): 이벤트 타임스탬프 (마이크로초)
- event_name (STRING): 이벤트 이름 (page_view, purchase, add_to_cart, session_start 등)
- event_value_in_usd (FLOAT): 이벤트 값 (USD)
- user_id (STRING): 사용자 ID
- user_pseudo_id (STRING): 익명 사용자 ID

중첩된 구조체:
- device.category (STRING): 기기 카테고리 (mobile, desktop, tablet)
- device.operating_system (STRING): 운영체제 (iOS, Android, Windows 등)
- device.mobile_brand_name (STRING): 모바일 브랜드명
- geo.country (STRING): 국가
- geo.region (STRING): 지역
- geo.city (STRING): 도시
- traffic_source.name (STRING): 트래픽 소스명
- traffic_source.medium (STRING): 매체
- traffic_source.source (STRING): 소스
- app_info.id (STRING): 앱 ID
- platform (STRING): 플랫폼 (WEB, IOS, ANDROID)

이벤트 매개변수 (event_params 배열):
- event_params 배열에서 특정 매개변수 추출 방법:
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title')
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')

전자상거래 정보:
- ecommerce.purchase_revenue (FLOAT): 구매 매출
- ecommerce.purchase_revenue_in_usd (FLOAT): USD 구매 매출

중요한 BigQuery 함수:
- TIMESTAMP_MICROS(event_timestamp): 타임스탬프를 날짜시간으로 변환
- EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp)): 시간 추출
- PARSE_DATE('%Y%m%d', event_date): 문자열 날짜를 DATE 타입으로 변환

"""
    
    return schema_text

def natural_language_to_sql(question):
    """자연어 질문을 BigQuery SQL로 변환"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    schema_prompt = get_schema_prompt()
    
    system_prompt = f"""당신은 BigQuery SQL 전문가이며, GA4 (Google Analytics 4) 데이터 분석에 특화되어 있습니다. 
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

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": question}
            ]
        )
        
        sql_query = response.content[0].text.strip()
        print(f"생성된 SQL: {sql_query}")  # 디버깅용
        return sql_query
        
    except Exception as e:
        raise Exception(f"Claude API 호출 중 오류 발생: {str(e)}")

def debug_bigquery_result(results):
    """BigQuery 결과 구조 디버깅"""
    for i, row in enumerate(results):
        print(f"Row {i} type: {type(row)}")
        print(f"Row {i} content: {row}")
        if hasattr(row, '__dict__'):
            print(f"Row {i} dict: {row.__dict__}")
        if i >= 2:  # 처음 3개만 확인
            break

def safe_row_to_dict(row):
    """BigQuery Row를 안전하게 딕셔너리로 변환"""
    try:
        # 방법 1: _asdict() 사용
        if hasattr(row, '_asdict'):
            return dict(row._asdict())
        
        # 방법 2: 직접 딕셔너리 변환
        elif hasattr(row, 'keys') and hasattr(row, 'values'):
            return {k: v for k, v in zip(row.keys(), row.values())}
        
        # 방법 3: 인덱스 기반 접근
        elif hasattr(row, '_fields'):
            return {field: getattr(row, field) for field in row._fields}
        
        # 방법 4: 최후의 수단
        else:
            return dict(row)
            
    except Exception as e:
        print(f"Row 변환 실패: {e}")
        return {"error": str(e), "raw_data": str(row)}

def execute_bigquery(sql_query):
    """개선된 BigQuery 실행 함수"""
    try:
        query_job = bigquery_client.query(sql_query)
        results = query_job.result()
        
        rows = []
        # 기존 코드를 다음으로 교체
        for row in results:
            try:
                # 1. 먼저 타입 확인
                if isinstance(row, str):
                    rows.append({"error": "Row is string", "content": row})
                    continue
                
                # 2. 딕셔너리 변환 시도
                if hasattr(row, '_asdict'):
                    row_dict = dict(row._asdict())
                else:
                    row_dict = dict(row)
                
                # 3. 안전한 타입 변환
                safe_row = {}
                for k, v in row_dict.items():
                    if isinstance(v, datetime):
                        safe_row[k] = v.isoformat()
                    else:
                        safe_row[k] = v
                
                rows.append(safe_row)
                
            except Exception as e:
                rows.append({"conversion_error": str(e), "raw_row": str(row)})
        
        return {
            "success": True,
            "data": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

def suggest_chart_config(data, columns):
    """데이터 구조를 분석하여 적절한 차트 설정 제안"""
    if not data or len(data) == 0:
        return None
    
    # 컬럼 개수에 따른 차트 타입 결정
    if len(columns) == 1:
        return None  # 단일 컬럼은 차트로 표현하기 어려움
    
    if len(columns) == 2:
        # 2개 컬럼인 경우
        col1, col2 = columns[0], columns[1]
        
        # 첫 번째 값으로 데이터 타입 판단
        first_val1 = data[0][col1] if data[0][col1] is not None else ""
        first_val2 = data[0][col2] if data[0][col2] is not None else 0
        
        # 두 번째 컬럼이 숫자인 경우
        if isinstance(first_val2, (int, float)):
            # 첫 번째 컬럼이 카테고리인 경우
            if isinstance(first_val1, str):
                return {
                    "type": "bar",
                    "label_column": col1,
                    "value_column": col2,
                    "title": f"{col1}별 {col2}"
                }
    
    # 3개 이상 컬럼인 경우 첫 번째는 라벨, 나머지는 값으로 가정
    if len(columns) >= 3:
        label_col = columns[0]
        value_cols = columns[1:]
        
        # 모든 값 컬럼이 숫자인지 확인
        all_numeric = True
        for col in value_cols:
            if data[0][col] is not None and not isinstance(data[0][col], (int, float)):
                all_numeric = False
                break
        
        if all_numeric:
            return {
                "type": "line" if len(value_cols) > 1 else "bar",
                "label_column": label_col,
                "value_columns": value_cols,
                "title": f"{label_col}별 데이터 비교"
            }
    
    return None

def analyze_data_structure(data):
    """데이터 구조를 분석하여 통계 요약 생성"""
    if not data or len(data) == 0:
        return {
            "row_count": 0,
            "columns": {},
            "summary_stats": {},
            "patterns": []
        }
    
    # 데이터 타입 검증
    if not isinstance(data, list):
        print(f"경고: 데이터가 리스트가 아닙니다: {type(data)}")
        return {
            "row_count": 0,
            "columns": {},
            "summary_stats": {},
            "patterns": ["데이터 타입 오류"]
        }
    
    # 첫 번째 행 검증
    if not data or not isinstance(data[0], dict):
        print(f"경고: 첫 번째 행이 딕셔너리가 아닙니다: {type(data[0]) if data else 'None'}")
        return {
            "row_count": len(data),
            "columns": {},
            "summary_stats": {},
            "patterns": ["데이터 구조 오류"]
        }
    
    analysis = {
        "row_count": len(data),
        "columns": {},
        "summary_stats": {},
        "patterns": []
    }
    
    # 각 컬럼별 분석
    try:
        for col in data[0].keys():
            # 안전한 값 추출
            values = []
            for row in data:
                if isinstance(row, dict) and col in row:
                    val = row[col]
                    if val is not None:
                        values.append(val)
            
            non_null_count = len(values)
            null_count = len(data) - non_null_count
            
            col_analysis = {
                "type": "unknown",
                "non_null_count": non_null_count,
                "null_count": null_count,
                "null_percentage": round((null_count / len(data)) * 100, 1) if len(data) > 0 else 0
            }
            
            if values:
                # 데이터 타입 판단
                first_val = values[0]
                if isinstance(first_val, (int, float)):
                    col_analysis["type"] = "numeric"
                    try:
                        numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                        if numeric_values:
                            col_analysis.update({
                                "min": min(numeric_values),
                                "max": max(numeric_values),
                                "mean": round(sum(numeric_values) / len(numeric_values), 2),
                                "median": round(sorted(numeric_values)[len(numeric_values)//2], 2),
                                "sum": sum(numeric_values)
                            })
                    except Exception as e:
                        print(f"숫자 분석 중 오류: {e}")
                        
                elif isinstance(first_val, str):
                    col_analysis["type"] = "categorical"
                    try:
                        unique_values = list(set(values))
                        col_analysis.update({
                            "unique_count": len(unique_values),
                            "most_common": max(set(values), key=values.count) if values else None,
                            "top_values": dict(sorted(
                                [(v, values.count(v)) for v in set(values[:100])], # 성능을 위해 상위 100개만 처리
                                key=lambda x: x[1], reverse=True
                            )[:5])
                        })
                    except Exception as e:
                        print(f"카테고리 분석 중 오류: {e}")
                        col_analysis["unique_count"] = len(set(str(v) for v in values[:100]))
            
            analysis["columns"][col] = col_analysis
            
    except Exception as e:
        print(f"데이터 구조 분석 중 오류: {e}")
        analysis["patterns"].append(f"분석 중 오류 발생: {str(e)}")
    
    return analysis

def generate_summary_insights(data_analysis, question):
    """데이터 분석 결과를 기반으로 핵심 인사이트 생성"""
    insights = []
    
    # 데이터 크기 인사이트
    row_count = data_analysis["row_count"]
    if row_count > 1000:
        insights.append(f"📊 **대용량 데이터셋**: {row_count:,}개의 레코드로 구성된 상당한 규모의 데이터입니다.")
    elif row_count < 10:
        insights.append(f"📊 **소규모 데이터셋**: {row_count}개의 레코드로 제한적인 샘플입니다.")
    
    # 컬럼별 인사이트
    for col, stats in data_analysis["columns"].items():
        if stats["type"] == "numeric":
            if "sum" in stats and stats["sum"] > 0:
                insights.append(f"🔢 **{col}**: 총합 {stats['sum']:,}, 평균 {stats['mean']:,}, 범위 {stats['min']:,}~{stats['max']:,}")
        elif stats["type"] == "categorical":
            if stats["unique_count"] < row_count * 0.5:  # 중복이 많은 경우
                top_value = list(stats["top_values"].items())[0] if stats["top_values"] else None
                if top_value:
                    percentage = round((top_value[1] / row_count) * 100, 1)
                    insights.append(f"📈 **{col}**: '{top_value[0]}'이 {percentage}%로 가장 높은 비중을 차지합니다.")
    
    return insights

def generate_analysis_report(question, sql_query, query_results, max_rows_for_analysis=100):
    """Claude Console 스타일의 분석 리포트 생성"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    if not query_results or len(query_results) == 0:
        return {"report": "분석할 데이터가 없습니다.", "chart_config": None, "data_summary": None}
    
    # 데이터 구조 분석
    data_analysis = analyze_data_structure(query_results)
    summary_insights = generate_summary_insights(data_analysis, question)
    
    # 샘플링
    sample_data = query_results[:max_rows_for_analysis] if len(query_results) > max_rows_for_analysis else query_results
    columns = list(sample_data[0].keys()) if sample_data else []
    
    # 차트 설정 제안
    chart_config = suggest_chart_config(query_results, columns)
    
    # Claude Console 스타일 데이터 요약 생성
    data_summary = {
        "overview": {
            "total_rows": len(query_results),
            "columns_count": len(columns),
            "data_types": {col: stats["type"] for col, stats in data_analysis["columns"].items()}
        },
        "key_statistics": data_analysis["columns"],
        "quick_insights": summary_insights
    }
    
    analysis_prompt = f"""다음은 GA4 데이터 분석 결과입니다. Claude Console과 같은 스타일로 구조화된 분석 리포트를 작성해주세요.

**원본 질문:** {question}

**데이터 개요:**
- 총 레코드 수: {data_analysis['row_count']:,}개
- 컬럼 수: {len(columns)}개
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

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        analysis_report = response.content[0].text.strip()
        
        return {
            "report": analysis_report,
            "chart_config": chart_config,
            "data_summary": data_summary
        }
        
    except Exception as e:
        raise Exception(f"분석 리포트 생성 중 오류 발생: {str(e)}")

def validate_claude_html(html_content):
    """Claude 생성 HTML 품질 검증"""
    issues = []
    
    # 기본 HTML 구조 검증
    if not html_content.strip().startswith('<!DOCTYPE'):
        issues.append("DOCTYPE 선언 누락")
    
    # Chart.js 링크 확인
    if 'Chart.js' in html_content and 'cdnjs.cloudflare.com' not in html_content:
        issues.append("Chart.js CDN 링크 누락")
    
    # 위험한 스크립트 패턴 확인
    dangerous_patterns = ['document.location', 'window.location', 'eval(', 'innerHTML']
    for pattern in dangerous_patterns:
        if pattern in html_content:
            issues.append(f"위험한 패턴 감지: {pattern}")
    
    # JavaScript 문법 간단 검증
    if 'new Chart(' in html_content and 'ctx' not in html_content:
        issues.append("Chart.js 컨텍스트 설정 누락")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "score": max(0, 100 - len(issues) * 20)  # 품질 점수
    }

def generate_fallback_html(question, query_results):
    """HTML 생성 실패 시 폴백 HTML"""
    # 안전한 데이터 처리
    if not isinstance(query_results, list):
        query_results = []
    
    result_count = len(query_results)
    
    # 테이블 생성 (안전하게)
    table_html = ""
    if result_count > 0 and isinstance(query_results[0], dict):
        try:
            headers = list(query_results[0].keys())
            table_html = f"""
            <table class="data-table">
                <thead>
                    <tr>
                        {''.join([f'<th>{str(col)}</th>' for col in headers])}
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"<tr>{''.join([f'<td>{str(row.get(col, ""))}</td>' for col in headers])}</tr>" 
                        for row in query_results[:10]
                    ])}
                </tbody>
            </table>
            """
        except Exception as e:
            print(f"폴백 테이블 생성 중 오류: {e}")
            table_html = f"<p>데이터 표시 중 오류가 발생했습니다: {str(e)}</p>"
    else:
        table_html = "<p>표시할 데이터가 없습니다.</p>"
    
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{question} - 분석 결과</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; color: #333; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .data-table th {{ background: #4285f4; color: white; padding: 12px; text-align: left; }}
            .data-table td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            .summary {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 {question}</h1>
                <p>GA4 데이터 분석 결과 • {result_count}개 결과</p>
            </div>
            
            <div class="warning">
                <h3>⚠️ 기본 리포트</h3>
                <p>고급 HTML 리포트 생성에 실패하여 기본 형태로 표시합니다.</p>
            </div>
            
            <div class="summary">
                <h3>📋 데이터 요약</h3>
                <p>총 {result_count}개의 레코드가 조회되었습니다.</p>
            </div>
            
            {table_html}
            
            <div class="summary">
                <p><em>더 나은 분석을 위해서는 "구조화 분석" 모드를 사용해보세요.</em></p>
            </div>
        </div>
    </body>
    </html>
    """

def safe_json_serialize(obj):
    """JSON 직렬화를 안전하게 수행하는 함수"""
    try:
        if isinstance(obj, dict):
            return {str(k): safe_json_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [safe_json_serialize(item) for item in obj]
        elif isinstance(obj, (datetime, )):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        else:
            return str(obj)
    except Exception as e:
        print(f"JSON 직렬화 오류: {e}")
        return str(obj)

def generate_html_analysis_report(question, sql_query, query_results):
    """Claude가 완전한 HTML 분석 리포트 생성 (검증 포함)"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    # 안전한 데이터 타입 검증
    try:
        if not query_results:
            query_results = []
        elif not isinstance(query_results, list):
            print(f"경고: query_results가 리스트가 아닙니다: {type(query_results)}")
            query_results = []
        
        if len(query_results) == 0:
            return {
                "html_content": generate_fallback_html(question, []),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
        # 첫 번째 행 검증
        if query_results and not isinstance(query_results[0], dict):
            print(f"경고: 첫 번째 데이터 행이 딕셔너리가 아닙니다: {type(query_results[0])}")
            return {
                "html_content": generate_fallback_html(question, query_results),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
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
                print(f"차트 데이터 변환 중 오류: {e}")
                chart_data = []
                chart_labels = []
        
        # 안전한 JSON 직렬화를 위한 데이터 정리
        safe_sample_data = safe_json_serialize(sample_data[:3])
        safe_chart_labels = safe_json_serialize(chart_labels[:5])
        safe_chart_data = safe_json_serialize(chart_data[:5])
        
        analysis_prompt = f"""다음 GA4 데이터 분석 결과를 완전한 HTML 페이지로 생성해주세요.

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

        max_attempts = 2
        
        for attempt in range(max_attempts):
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=[
                        {"role": "user", "content": analysis_prompt}
                    ]
                )
                
                html_content = response.content[0].text.strip()
                
                # HTML 태그 확인 및 정리
                if not html_content.startswith('<!DOCTYPE') and not html_content.startswith('<html'):
                    # Claude가 마크다운 블록으로 감쌌을 수 있음
                    if '```html' in html_content:
                        html_content = html_content.split('```html')[1].split('```')[0].strip()
                    elif '```' in html_content:
                        html_content = html_content.split('```')[1].strip()
                
                # HTML 품질 검증
                validation = validate_claude_html(html_content)
                
                if validation["is_valid"] or validation["score"] >= 70:
                    return {
                        "html_content": html_content,
                        "quality_score": validation["score"],
                        "attempts": attempt + 1,
                        "issues": validation.get("issues", []),
                        "fallback": False
                    }
                
                if attempt < max_attempts - 1:
                    print(f"HTML 품질 개선 필요 (점수: {validation['score']}), 재시도 중...")
                    
            except Exception as e:
                print(f"HTML 생성 시도 {attempt + 1} 실패: {str(e)}")
        
        # 모든 시도 실패 시 폴백
        return {
            "html_content": generate_fallback_html(question, query_results),
            "quality_score": 60,
            "attempts": max_attempts,
            "fallback": True
        }
        
    except Exception as e:
        print(f"HTML 분석 리포트 생성 중 예상치 못한 오류: {e}")
        return {
            "html_content": generate_fallback_html(question, []),
            "quality_score": 50,
            "attempts": 1,
            "fallback": True
        }

# API 엔드포인트들

@app.route('/quick', methods=['POST'])
def quick_query():
    """빠른 조회 - 데이터만 반환"""
    try:
        # 요청 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다.",
                "mode": "quick"
            }), 400

        question = request.json['question'].strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다.",
                "mode": "quick"
            }), 400
        
        # SQL 생성 및 데이터 조회
        sql_query = natural_language_to_sql(question)
        query_result = execute_bigquery(sql_query)
        
        if not query_result["success"]:
            return jsonify({
                "success": False,
                "error": query_result["error"],
                "mode": "quick",
                "original_question": question,
                "generated_sql": sql_query
            }), 500
        
        return jsonify({
            "success": True,
            "mode": "quick",
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0)
        })
        
    except Exception as e:
        print(f"빠른 조회 중 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "quick"
        }), 500

@app.route('/analyze', methods=['POST'])
def structured_analysis():
    """구조화된 분석 - 차트와 분석 리포트 포함"""
    try:
        # 요청 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다.",
                "mode": "structured"
            }), 400

        question = request.json['question'].strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다.",
                "mode": "structured"
            }), 400
        
        # SQL 생성 및 데이터 조회
        sql_query = natural_language_to_sql(question)
        query_result = execute_bigquery(sql_query)
        
        if not query_result["success"]:
            return jsonify({
                "success": False,
                "error": query_result["error"],
                "mode": "structured",
                "original_question": question,
                "generated_sql": sql_query
            }), 500
        
        # 구조화된 분석 리포트 생성
        analysis_result = generate_analysis_report(
            question, 
            sql_query, 
            query_result["data"]
        )
        
        return jsonify({
            "success": True,
            "mode": "structured",
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0),
            "analysis_report": analysis_result["report"],
            "chart_config": analysis_result["chart_config"],
            "data_summary": analysis_result["data_summary"]
        })
        
    except Exception as e:
        print(f"구조화된 분석 중 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "structured"
        }), 500

@app.route('/creative-html', methods=['POST'])
def creative_html_analysis():
    """창의적 HTML 분석 - Claude가 완전한 HTML 생성"""
    try:
        # 요청 데이터 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다.",
                "mode": "creative_html"
            }), 400

        question = request.json['question'].strip()
        
        if not question:
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다.",
                "mode": "creative_html"
            }), 400
        
        # SQL 생성 및 데이터 조회
        try:
            sql_query = natural_language_to_sql(question)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"SQL 변환 중 오류: {str(e)}",
                "mode": "creative_html",
                "original_question": question
            }), 500
        
        query_result = execute_bigquery(sql_query)
        
        if not query_result["success"]:
            return jsonify({
                "success": False,
                "error": query_result["error"],
                "mode": "creative_html",
                "original_question": question,
                "generated_sql": sql_query
            }), 500
        
        # 데이터 타입 및 구조 검증
        data = query_result.get("data", [])
        if not isinstance(data, list):
            print(f"경고: 쿼리 결과 데이터가 리스트가 아닙니다: {type(data)}")
            data = []
        
        # Claude HTML 생성
        try:
            html_result = generate_html_analysis_report(
                question, 
                sql_query, 
                data
            )
        except Exception as e:
            print(f"HTML 생성 중 오류: {str(e)}")
            # 오류 시 폴백 HTML 생성
            html_result = {
                "html_content": generate_fallback_html(question, data),
                "quality_score": 50,
                "attempts": 1,
                "fallback": True
            }
        
        return jsonify({
            "success": True,
            "mode": "creative_html",
            "original_question": question,
            "generated_sql": sql_query,
            "row_count": query_result.get("row_count", len(data)),
            "html_content": html_result["html_content"],
            "quality_score": html_result["quality_score"],
            "attempts": html_result["attempts"],
            "is_fallback": html_result.get("fallback", False)
        })
        
    except Exception as e:
        print(f"창의적 HTML 분석 중 예상치 못한 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "creative_html"
        }), 500

# 기존 엔드포인트들 (하위 호환성)
@app.route('/query', methods=['POST'])
def legacy_query():
    """기존 호환성을 위한 엔드포인트 - 구조화된 분석으로 리다이렉트"""
    return structured_analysis()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "project_id": PROJECT_ID,
        "table": f"{PROJECT_ID}.test_dataset.events_20201121",
        "bigquery_client_project": bigquery_client.project if bigquery_client else "Not initialized",
        "services": {
            "anthropic": "configured" if ANTHROPIC_API_KEY else "not configured",
            "bigquery": "configured (using ADC)" if bigquery_client else "not configured"
        },
        "supported_modes": ["quick", "structured", "creative_html"]
    })

@app.route('/schema', methods=['GET'])
def get_schema():
    """테이블 스키마 정보 조회 엔드포인트"""
    return jsonify({
        "success": True,
        "project_id": PROJECT_ID,
        "table": f"{PROJECT_ID}.test_dataset.events_20201121",
        "schema": TABLE_SCHEMA
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "엔드포인트를 찾을 수 없습니다."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "내부 서버 오류가 발생했습니다."
    }), 500

if __name__ == '__main__':
    # 환경 변수 확인
    if not ANTHROPIC_API_KEY:
        print("경고: ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    if not bigquery_client:
        print("경고: BigQuery 클라이언트가 초기화되지 않았습니다.")
    
    print(f"프로젝트 ID: {PROJECT_ID}")
    print(f"테이블: {PROJECT_ID}.test_dataset.events_20201121")
    print("지원 모드: 빠른 조회(/quick), 구조화된 분석(/analyze), 창의적 HTML(/creative-html)")
    
    # Cloud Run에서는 PORT 환경변수 사용
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)