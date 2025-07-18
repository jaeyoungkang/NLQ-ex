from flask import Flask, request, jsonify, send_from_directory
from google.cloud import bigquery
import anthropic
import os
import json
import re
import traceback
from datetime import datetime

app = Flask(__name__)

# ==============================================================================
# 1. 초기 설정 및 클라이언트 초기화
# ==============================================================================

# 환경 변수에서 API 키 읽기
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    print("경고: ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

# Anthropic 클라이언트 초기화
try:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except Exception as e:
    print(f"Anthropic 클라이언트 초기화 실패: {e}")
    anthropic_client = None

# BigQuery 클라이언트 초기화 (프로젝트 ID 명시)
PROJECT_ID = "nlq-ex"
try:
    bigquery_client = bigquery.Client(project=PROJECT_ID)
except Exception as e:
    print(f"BigQuery 클라이언트 초기화 실패: {e}")
    bigquery_client = None

# GA4 Events 테이블 스키마 정보 (기존과 동일)
TABLE_SCHEMA = {
    "events_20201121": {
        "description": "GA4 이벤트 데이터 (2020년 11월 21일)",
        "columns": [
            {"name": "event_date", "type": "STRING", "description": "이벤트 날짜 (YYYYMMDD 형식)"},
            {"name": "event_timestamp", "type": "INTEGER", "description": "이벤트 타임스탬프 (마이크로초)"},
            {"name": "event_name", "type": "STRING", "description": "이벤트 이름 (page_view, purchase, add_to_cart 등)"},
            {"name": "user_pseudo_id", "type": "STRING", "description": "익명 사용자 ID"},
            {"name": "device", "type": "RECORD", "description": "기기 정보 (category, mobile_brand_name, operating_system 등)"},
            {"name": "geo", "type": "RECORD", "description": "지리적 정보 (country, region, city 등)"},
            {"name": "event_params", "type": "RECORD", "description": "이벤트 매개변수 (중첩된 키-값 쌍)"},
            {"name": "ecommerce", "type": "RECORD", "description": "전자상거래 정보 (purchase_revenue, items 등)"},
        ],
    }
}


# ==============================================================================
# 2. 핵심 로직 함수 (수정 및 개선됨)
# ==============================================================================

def get_schema_prompt():
    """GA4 테이블 스키마 정보를 프롬프트 형태로 변환 (기존과 동일)"""
    # ... (기존 코드와 동일하여 생략)
    return "..." # 실제 프롬프트 내용

def natural_language_to_sql(question):
    """자연어 질문을 BigQuery SQL로 변환 (기존과 동일)"""
    # ... (기존 코드와 동일하여 생략)
    return "SELECT 1;" # 실제 SQL 생성 로직

def _convert_row_to_dict(row):
    """
    [개선됨] BigQuery Row를 재귀적으로 순수 파이썬 딕셔너리로 변환합니다.
    중첩된 RECORD나 ARRAY도 안전하게 처리합니다.
    """
    if not hasattr(row, 'items'):
        return row

    row_dict = {}
    for key, value in row.items():
        if hasattr(value, 'items'):  # 중첩된 Row/Record인 경우
            row_dict[key] = _convert_row_to_dict(value)
        elif isinstance(value, list): # 배열(ARRAY)인 경우
            row_dict[key] = [_convert_row_to_dict(item) if hasattr(item, 'items') else item for item in value]
        elif isinstance(value, datetime): # 날짜/시간 객체인 경우
            row_dict[key] = value.isoformat()
        else:
            row_dict[key] = value
    return row_dict

def execute_bigquery(sql_query):
    """[개선됨] BigQuery에서 SQL 쿼리를 실행하고 결과를 안전하게 변환합니다."""
    if not bigquery_client:
        raise Exception("BigQuery 클라이언트가 초기화되지 않았습니다.")
    try:
        print(f"실행할 SQL: {sql_query}")
        query_job = bigquery_client.query(sql_query)
        results = query_job.result()
        
        # 재귀 변환 함수를 사용하여 결과를 안전한 딕셔너리 리스트로 변환
        rows = [_convert_row_to_dict(row) for row in results]
        
        return {"success": True, "data": rows, "row_count": len(rows)}
    except Exception as e:
        print(f"BigQuery 실행 중 오류 발생: {e}")
        traceback.print_exc()  # 상세한 오류 로그 출력
        return {"success": False, "error": str(e), "data": []}

def analyze_data_structure(data):
    """[개선됨] 데이터 구조를 더욱 안전하게 분석하여 통계 요약을 생성합니다."""
    if not data or not isinstance(data, list) or not isinstance(data[0], dict):
        return {}

    analysis = {
        "row_count": len(data),
        "columns": {},
        "summary_stats": {},
        "patterns": []
    }
    
    # 모든 행에서 가능한 모든 키를 수집 (더 이상 첫 번째 행에 의존하지 않음)
    all_keys = set()
    for row in data:
        if isinstance(row, dict):
            all_keys.update(row.keys())

    for col in sorted(list(all_keys)):
        # .get()을 사용하고 타입 검사를 하여 안전하게 값 추출
        values = [row.get(col) for row in data if isinstance(row, dict) and row.get(col) is not None]
        
        non_null_count = len(values)
        null_count = len(data) - non_null_count
        
        col_analysis = {
            "type": "unknown",
            "non_null_count": non_null_count,
            "null_count": null_count,
            "null_percentage": round((null_count / len(data)) * 100, 1) if len(data) > 0 else 0
        }
        
        if values:
            first_val = values[0]
            if isinstance(first_val, (int, float)):
                col_analysis["type"] = "numeric"
                # ... (이하 로직은 기존과 유사하게 안전하게 처리)
            elif isinstance(first_val, str):
                col_analysis["type"] = "categorical"
                # ... (이하 로직은 기존과 유사하게 안전하게 처리)
            elif isinstance(first_val, dict):
                col_analysis["type"] = "nested_object"
            elif isinstance(first_val, list):
                col_analysis["type"] = "array"

        analysis["columns"][col] = col_analysis
    
    return analysis

# generate_summary_insights, suggest_chart_config 등 다른 분석 함수들은
# 위에서 개선된 analyze_data_structure 덕분에 더 안정적으로 동작하게 됩니다.
# (코드가 길어 생략, 기존 코드 사용)

def generate_analysis_report(question, sql_query, query_results):
    # ... (기존 코드와 동일)
    return {"report": "...", "chart_config": {...}, "data_summary": {...}}

def generate_html_analysis_report(question, sql_query, query_results):
    # ... (기존 코드와 동일)
    return {"html_content": "...", "quality_score": 100, "attempts": 1, "fallback": False}

# ==============================================================================
# 3. API 엔드포인트 (오류 처리 강화)
# ==============================================================================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/analyze', methods=['POST'])
def structured_analysis():
    """구조화된 분석 - 차트와 분석 리포트 포함 (오류 처리 강화)"""
    try:
        if not request.json or 'question' not in request.json:
            return jsonify({"success": False, "error": "요청 본문에 'question' 필드가 필요합니다."}), 400
        question = request.json['question'].strip()
        if not question:
            return jsonify({"success": False, "error": "질문이 비어있습니다."}), 400
        
        sql_query = natural_language_to_sql(question)
        query_result = execute_bigquery(sql_query)
        
        if not query_result["success"]:
            return jsonify({**query_result, "mode": "structured"}), 500
        
        analysis_result = generate_analysis_report(question, sql_query, query_result["data"])
        
        return jsonify({
            "success": True, "mode": "structured", "original_question": question,
            "generated_sql": sql_query, "data": query_result["data"],
            "row_count": query_result.get("row_count", 0), **analysis_result,
        })
        
    except Exception as e:
        print(f"'/analyze' 엔드포인트에서 처리되지 않은 예외 발생: {e}")
        traceback.print_exc()  # 상세한 오류 로그 출력
        return jsonify({"success": False, "error": f"서버 오류: {str(e)}", "mode": "structured"}), 500

# /quick, /creative-html 엔드포인트도 위와 같이 try-except 블록에 traceback.print_exc() 추가
# (코드가 길어 생략)


# ==============================================================================
# 4. 앱 설정 및 실행 (CORS 추가)
# ==============================================================================

@app.after_request
def after_request(response):
    """[추가됨] 모든 응답에 CORS 헤더를 추가합니다."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.errorhandler(500)
def internal_error(error):
    """[개선됨] 500 오류 발생 시 상세 로그를 남깁니다."""
    print(f"500 내부 서버 오류: {error}")
    traceback.print_exc()
    return jsonify({"success": False, "error": "내부 서버 오류가 발생했습니다."}), 500

if __name__ == '__main__':
    print("🚀 GA4 자연어 분석 서버 시작")
    if not ANTHROPIC_API_KEY: print("   - Anthropic API 키가 설정되지 않았습니다.")
    if not bigquery_client: print("   - BigQuery 클라이언트가 초기화되지 않았습니다.")
    
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)