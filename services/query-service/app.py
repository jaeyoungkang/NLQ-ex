# services/query-service/app.py
from flask import Flask, request, jsonify
from google.cloud import bigquery
import anthropic
import os
import json

app = Flask(__name__)

# 설정
PROJECT_ID = "nlq-ex"
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# 클라이언트 초기화
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
bigquery_client = bigquery.Client(project=PROJECT_ID)

# 스키마 정보
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
            # BigQuery Row 객체를 딕셔너리로 변환
            row_dict = {}
            
            # Row 객체의 keys()와 values()를 사용하여 안전하게 변환
            try:
                # BigQuery Row 객체를 딕셔너리로 변환하는 안전한 방법
                if hasattr(row, 'keys') and hasattr(row, 'values'):
                    for key, value in zip(row.keys(), row.values()):
                        # BigQuery의 특수 타입들을 JSON 직렬화 가능한 형태로 변환
                        if isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                        elif hasattr(value, 'isoformat'):  # date, time 객체
                            row_dict[key] = value.isoformat()
                        else:
                            row_dict[key] = value
                else:
                    # 대안적인 변환 방법
                    row_dict = dict(row)
                    # 타입 변환 처리
                    for key, value in row_dict.items():
                        if isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                        elif hasattr(value, 'isoformat'):
                            row_dict[key] = value.isoformat()
                        
            except Exception as e:
                print(f"Row 변환 중 오류: {e}")
                # 최후의 수단으로 문자열 변환
                try:
                    row_dict = {f"col_{i}": str(val) for i, val in enumerate(row)}
                except Exception as inner_e:
                    print(f"문자열 변환 중 오류: {inner_e}")
                    row_dict = {"error": f"Row 변환 실패: {str(e)}"}
            
            rows.append(row_dict)
        
        print(f"변환된 행 수: {len(rows)}")  # 디버깅용
        if rows:
            print(f"첫 번째 행 타입: {type(rows[0])}")  # 디버깅용
            print(f"첫 번째 행 키: {list(rows[0].keys()) if isinstance(rows[0], dict) else 'Not a dict'}")  # 디버깅용
        
        return {
            "success": True,
            "data": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:

@app.route('/quick', methods=['POST'])
def quick_query():
    """빠른 조회"""
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({"success": False, "error": "질문이 필요합니다"}), 400
    
    try:
        sql_query = natural_language_to_sql(question)
        result = execute_bigquery(sql_query)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "original_question": question,
                "generated_sql": sql_query,
                "data": result["data"],
                "row_count": result["row_count"]
            })
        else:
            return jsonify({"success": False, "error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_query():
    """SQL 실행만 담당"""
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({"success": False, "error": "질문이 필요합니다"}), 400
    
    try:
        sql_query = natural_language_to_sql(question)
        result = execute_bigquery(sql_query)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "original_question": question,
                "generated_sql": sql_query,
                "data": result["data"],
                "row_count": result["row_count"]
            })
        else:
            return jsonify({"success": False, "error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/schema')
def get_schema():
    """스키마 정보 반환"""
    return jsonify(TABLE_SCHEMA)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "query-service"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)