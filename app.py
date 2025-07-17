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

# BigQuery 클라이언트 초기화 (ADC 사용)
try:
    bigquery_client = bigquery.Client()
    PROJECT_ID = bigquery_client.project
    print(f"BigQuery 프로젝트 ID: {PROJECT_ID}")
except Exception as e:
    print(f"BigQuery 클라이언트 초기화 실패: {e}")
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')

# 샘플 테이블 스키마 정보 (수정된 버전)
TABLE_SCHEMA = {
    "users": {
        "columns": [
            {"name": "user_id", "type": "INTEGER", "description": "사용자 고유 ID"},
            {"name": "name", "type": "STRING", "description": "사용자 이름"},
            {"name": "email", "type": "STRING", "description": "이메일 주소"},
            {"name": "created_at", "type": "TIMESTAMP", "description": "계정 생성일"},
            {"name": "age", "type": "INTEGER", "description": "나이"},
            {"name": "city", "type": "STRING", "description": "거주 도시"}
        ]
    },
    "orders": {
        "columns": [
            {"name": "order_id", "type": "INTEGER", "description": "주문 고유 ID"},
            {"name": "user_id", "type": "INTEGER", "description": "주문한 사용자 ID"},
            {"name": "product_name", "type": "STRING", "description": "상품명"},
            {"name": "amount", "type": "FLOAT", "description": "주문 금액"},
            {"name": "order_date", "type": "DATE", "description": "주문일"},
            {"name": "status", "type": "STRING", "description": "주문 상태 (pending, completed, cancelled)"}
        ]
    }
}

def get_schema_prompt():
    """테이블 스키마 정보를 프롬프트 형태로 변환"""
    schema_text = f"다음은 BigQuery 데이터베이스의 테이블 스키마 정보입니다 (프로젝트: {PROJECT_ID}):\n\n"
    
    for table_name, table_info in TABLE_SCHEMA.items():
        full_table_name = f"`{PROJECT_ID}.test_dataset.{table_name}`"
        schema_text += f"테이블: {full_table_name}\n"
        schema_text += "컬럼:\n"
        for column in table_info["columns"]:
            schema_text += f"  - {column['name']} ({column['type']}): {column['description']}\n"
        schema_text += "\n"
    
    return schema_text

def natural_language_to_sql(question):
    """자연어 질문을 BigQuery SQL로 변환"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    schema_prompt = get_schema_prompt()
    
    system_prompt = f"""당신은 BigQuery SQL 전문가입니다. 사용자의 자연어 질문을 BigQuery SQL 쿼리로 변환해주세요.

{schema_prompt}

중요한 규칙:
1. BigQuery 표준 SQL 문법을 사용해주세요.
2. 테이블 참조 시 반드시 백틱(`)을 사용하여 `{PROJECT_ID}.test_dataset.테이블명` 형식으로 사용하세요.
3. 날짜 관련 함수는 BigQuery 함수를 사용하세요 (예: CURRENT_DATE(), DATE_SUB() 등).
4. SQL 쿼리만 반환하고, 다른 설명은 포함하지 마세요.
5. 쿼리는 반드시 세미콜론(;)으로 끝나야 합니다.

사용 가능한 테이블:
- `{PROJECT_ID}.test_dataset.users` (사용자 정보)
- `{PROJECT_ID}.test_dataset.orders` (주문 정보)

예시:
질문: "사용자 수를 알려주세요"
답변: SELECT COUNT(*) as user_count FROM `{PROJECT_ID}.test_dataset.users`;

질문: "총 주문 수를 알려주세요"
답변: SELECT COUNT(*) as total_orders FROM `{PROJECT_ID}.test_dataset.orders`;

질문: "주문 상태별 개수를 보여주세요"
답변: SELECT status, COUNT(*) as order_count FROM `{PROJECT_ID}.test_dataset.orders` GROUP BY status;"""

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

@app.route('/query', methods=['POST'])
def process_natural_language_query():
    """자연어 질의 처리 API 엔드포인트"""
    try:
        # 요청 데이터 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다."
            }), 400
        
        question = request.json['question']
        
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
        "services": {
            "anthropic": "configured" if ANTHROPIC_API_KEY else "not configured",
            "bigquery": "configured (using ADC)"
        }
    })

@app.route('/schema', methods=['GET'])
def get_schema():
    """테이블 스키마 정보 조회 엔드포인트"""
    return jsonify({
        "success": True,
        "project_id": PROJECT_ID,
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
    
    print(f"프로젝트 ID: {PROJECT_ID}")
    
    # Cloud Run에서는 PORT 환경변수 사용
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)