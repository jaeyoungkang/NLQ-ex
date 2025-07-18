from flask import Flask, request, jsonify, send_from_directory
from google.cloud import bigquery
import anthropic
import os
import json
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

def execute_bigquery(sql_query):
    """BigQuery에서 SQL 쿼리 실행"""
    try:
        print(f"실행할 SQL: {sql_query}")  # 디버깅용
        print(f"사용 중인 프로젝트 ID: {bigquery_client.project}")  # 디버깅용
        
        # 쿼리 실행
        query_job = bigquery_client.query(sql_query)
        results = query_job.result()
        
        # 결과를 딕셔너리 리스트로 변환
        rows = []
        for row in results:
            row_dict = {}
            for key, value in row.items():
                # BigQuery의 특수 타입들을 JSON 직렬화 가능한 형태로 변환
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif hasattr(value, 'isoformat'):  # date, time 객체
                    row_dict[key] = value.isoformat()
                else:
                    row_dict[key] = value
            rows.append(row_dict)
        
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

def generate_analysis_report(question, sql_query, query_results, max_rows_for_analysis=100):
    """쿼리 결과를 Claude에게 보내서 분석 리포트 생성"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    if not query_results or len(query_results) == 0:
        return "분석할 데이터가 없습니다."
    
    # 데이터가 너무 많으면 샘플링
    sample_data = query_results[:max_rows_for_analysis] if len(query_results) > max_rows_for_analysis else query_results
    
    # 데이터 요약 정보 생성
    data_summary = {
        "total_rows": len(query_results),
        "sample_rows": len(sample_data),
        "columns": list(sample_data[0].keys()) if sample_data else [],
        "sample_data": sample_data[:10]  # 처음 10개 행만 샘플로
    }
    
    analysis_prompt = f"""다음은 GA4 데이터 분석 결과입니다. 이 데이터를 분석하여 인사이트가 풍부한 리포트를 작성해주세요.

**원본 질문:** {question}

**실행된 SQL 쿼리:**
```sql
{sql_query}
```

**데이터 요약:**
- 총 행 수: {data_summary['total_rows']:,}개
- 분석 대상: {data_summary['sample_rows']:,}개 행
- 컬럼: {', '.join(data_summary['columns'])}

**샘플 데이터 (상위 10개 행):**
{json.dumps(data_summary['sample_data'], indent=2, ensure_ascii=False, default=str)}

**분석 요청사항:**
1. 핵심 인사이트 3-5개를 도출해주세요
2. 데이터의 패턴이나 트렌드를 분석해주세요
3. 비즈니스 관점에서의 시사점을 제시해주세요
4. 추가 분석이 필요한 영역이 있다면 제안해주세요
5. 데이터 품질이나 특이사항이 있다면 언급해주세요

**리포트 형식:**
- 한국어로 작성
- 구조화된 마크다운 형식
- 구체적인 수치와 함께 설명
- 실행 가능한 제안사항 포함"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        analysis_report = response.content[0].text.strip()
        return analysis_report
        
    except Exception as e:
        raise Exception(f"분석 리포트 생성 중 오류 발생: {str(e)}")

@app.route('/query', methods=['POST'])
def process_natural_language_query():
    """자연어 질의 처리 API 엔드포인트 (분석 옵션 추가)"""
    try:
        # 요청 데이터 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다."
            }), 400
        
        question = request.json['question']
        include_analysis = request.json.get('include_analysis', False)  # 기본값은 False
        
        if not question.strip():
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다."
            }), 400
        
        # 1단계: 자연어를 SQL로 변환
        try:
            sql_query = natural_language_to_sql(question)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"SQL 변환 중 오류: {str(e)}"
            }), 500
        
        # 2단계: BigQuery에서 SQL 실행
        query_result = execute_bigquery(sql_query)
        
        # 응답 구성
        response = {
            "success": query_result["success"],
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0)
        }
        
        if not query_result["success"]:
            response["error"] = query_result["error"]
            return jsonify(response), 500
        
        # 3단계: 분석 리포트 생성 (요청된 경우만)
        if include_analysis and query_result["data"]:
            try:
                analysis_report = generate_analysis_report(
                    question, 
                    sql_query, 
                    query_result["data"]
                )
                response["analysis_report"] = analysis_report
            except Exception as e:
                response["analysis_error"] = f"분석 리포트 생성 실패: {str(e)}"
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_query_results():
    """쿼리 결과 분석 API 엔드포인트"""
    try:
        # 요청 데이터 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다."
            }), 400
        
        question = request.json['question']
        include_analysis = request.json.get('include_analysis', True)
        
        if not question.strip():
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다."
            }), 400
        
        # 1단계: 자연어를 SQL로 변환
        try:
            sql_query = natural_language_to_sql(question)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"SQL 변환 중 오류: {str(e)}"
            }), 500
        
        # 2단계: BigQuery에서 SQL 실행
        query_result = execute_bigquery(sql_query)
        
        if not query_result["success"]:
            return jsonify({
                "success": False,
                "error": query_result["error"],
                "original_question": question,
                "generated_sql": sql_query
            }), 500
        
        # 3단계: 분석 리포트 생성 (옵션)
        analysis_report = None
        if include_analysis and query_result["data"]:
            try:
                analysis_report = generate_analysis_report(
                    question, 
                    sql_query, 
                    query_result["data"]
                )
            except Exception as e:
                print(f"분석 리포트 생성 실패: {e}")
                analysis_report = f"분석 리포트 생성 중 오류 발생: {str(e)}"
        
        # 응답 구성
        response = {
            "success": True,
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0),
            "analysis_report": analysis_report
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}"
        }), 500

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
        }
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
    
    # Cloud Run에서는 PORT 환경변수 사용
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)