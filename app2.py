from flask import Flask, request, jsonify, send_from_directory
from google.cloud import bigquery
import anthropic
import os
import json
import re
import traceback
from datetime import datetime

app = Flask(__name__)

# 디버깅 함수
def debug_log(message, data=None):
    """디버깅 로그 출력"""
    print(f"[DEBUG] {message}")
    if data is not None:
        print(f"[DEBUG] Data type: {type(data)}")
        if hasattr(data, '__len__'):
            try:
                print(f"[DEBUG] Data length: {len(data)}")
            except:
                pass
        print(f"[DEBUG] Data content: {str(data)[:200]}...")

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

def natural_language_to_sql(question):
    """자연어 질문을 BigQuery SQL로 변환"""
    debug_log("SQL 변환 시작", question)
    
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    system_prompt = f"""당신은 BigQuery SQL 전문가입니다. 
사용자의 자연어 질문을 BigQuery SQL 쿼리로 변환해주세요.

테이블: `{PROJECT_ID}.test_dataset.events_20201121`

주요 컬럼:
- event_name (STRING): 이벤트 이름
- event_timestamp (INTEGER): 이벤트 타임스탬프 (마이크로초)
- user_pseudo_id (STRING): 익명 사용자 ID
- device.category (STRING): 기기 카테고리
- geo.country (STRING): 국가
- platform (STRING): 플랫폼

규칙:
1. BigQuery 표준 SQL 문법 사용
2. 테이블명은 백틱(`) 사용
3. SQL 쿼리만 반환 (설명 제외)
4. 세미콜론(;)으로 끝내기
5. 결과가 많을 때는 LIMIT 사용"""

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
        debug_log("생성된 SQL", sql_query)
        return sql_query
        
    except Exception as e:
        debug_log("Claude API 오류", str(e))
        raise Exception(f"Claude API 호출 중 오류 발생: {str(e)}")

def execute_bigquery(sql_query):
    """BigQuery에서 SQL 쿼리 실행"""
    debug_log("BigQuery 실행 시작", sql_query)
    
    try:
        if not bigquery_client:
            raise Exception("BigQuery 클라이언트가 초기화되지 않았습니다.")
        
        # 쿼리 실행
        query_job = bigquery_client.query(sql_query)
        results = query_job.result()
        
        debug_log("BigQuery 쿼리 실행 완료")
        
        # 결과를 딕셔너리 리스트로 변환
        rows = []
        row_count = 0
        
        for row in results:
            row_count += 1
            debug_log(f"처리 중인 행 {row_count}", f"Row type: {type(row)}")
            
            row_dict = {}
            
            # row.items() 대신 안전한 방법 사용
            try:
                if hasattr(row, 'items'):
                    items = row.items()
                elif hasattr(row, '_fields'):
                    # BigQuery Row 객체의 경우
                    items = [(field, getattr(row, field)) for field in row._fields]
                else:
                    debug_log("알 수 없는 행 타입", type(row))
                    continue
                
                for key, value in items:
                    debug_log(f"컬럼 처리: {key}", f"Value type: {type(value)}, Value: {value}")
                    
                    # 값 변환
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    elif hasattr(value, 'isoformat'):
                        row_dict[key] = value.isoformat()
                    elif value is None:
                        row_dict[key] = None
                    else:
                        row_dict[key] = value
                        
                rows.append(row_dict)
                debug_log(f"행 {row_count} 변환 완료", row_dict)
                
            except Exception as row_error:
                debug_log(f"행 {row_count} 처리 중 오류", str(row_error))
                print(f"[ERROR] Row processing error: {traceback.format_exc()}")
                continue
        
        debug_log("BigQuery 결과 변환 완료", f"총 {len(rows)}개 행")
        
        return {
            "success": True,
            "data": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:
        debug_log("BigQuery 실행 오류", str(e))
        print(f"[ERROR] BigQuery execution error: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

def create_simple_fallback_html(question, data_count=0):
    """매우 단순한 폴백 HTML"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>분석 결과</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ background: #4285f4; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {question}</h1>
        </div>
        <div class="content">
            <h2>분석 결과</h2>
            <p>총 {data_count}개의 결과가 조회되었습니다.</p>
            <p>기본 HTML 리포트로 표시되었습니다.</p>
        </div>
    </div>
</body>
</html>"""

def generate_creative_html_simple(question, sql_query, query_results):
    """단순화된 창의적 HTML 생성"""
    debug_log("창의적 HTML 생성 시작", f"Results type: {type(query_results)}")
    
    try:
        # 데이터 검증
        if not query_results:
            debug_log("결과 없음")
            return {
                "html_content": create_simple_fallback_html(question, 0),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
        if not isinstance(query_results, list):
            debug_log("결과가 리스트가 아님", type(query_results))
            return {
                "html_content": create_simple_fallback_html(question, 0),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
        data_count = len(query_results)
        debug_log(f"데이터 개수: {data_count}")
        
        if data_count == 0:
            return {
                "html_content": create_simple_fallback_html(question, 0),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
        # 첫 번째 행 검사
        first_row = query_results[0]
        debug_log("첫 번째 행", f"Type: {type(first_row)}, Content: {first_row}")
        
        if not isinstance(first_row, dict):
            debug_log("첫 번째 행이 딕셔너리가 아님")
            return {
                "html_content": create_simple_fallback_html(question, data_count),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
        # Claude로 HTML 생성 시도
        if not anthropic_client:
            debug_log("Anthropic 클라이언트 없음")
            return {
                "html_content": create_simple_fallback_html(question, data_count),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
        # 안전한 샘플 데이터 생성
        sample_size = min(3, data_count)
        sample_data = []
        
        for i in range(sample_size):
            try:
                row = query_results[i]
                if isinstance(row, dict):
                    safe_row = {}
                    for k, v in row.items():
                        safe_row[str(k)] = str(v) if v is not None else "NULL"
                    sample_data.append(safe_row)
                else:
                    debug_log(f"행 {i}가 딕셔너리가 아님", type(row))
            except Exception as e:
                debug_log(f"샘플 데이터 {i} 처리 오류", str(e))
        
        debug_log("샘플 데이터 생성 완료", sample_data)
        
        prompt = f"""다음 데이터를 기반으로 완전한 HTML 리포트를 생성해주세요.

질문: {question}
SQL: {sql_query}
데이터 수: {data_count}개
샘플: {json.dumps(sample_data, ensure_ascii=False)}

완전한 HTML 문서를 생성해주세요 (DOCTYPE부터 </html>까지).
Google 스타일의 깔끔한 디자인을 사용하고, 한국어로 작성해주세요."""

        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            html_content = response.content[0].text.strip()
            debug_log("Claude HTML 생성 완료", f"Length: {len(html_content)}")
            
            # HTML 정리
            if '```html' in html_content:
                html_content = html_content.split('```html')[1].split('```')[0].strip()
            elif '```' in html_content:
                html_content = html_content.split('```')[1].strip()
            
            if not html_content.startswith('<!DOCTYPE'):
                debug_log("HTML 형식 문제")
                return {
                    "html_content": create_simple_fallback_html(question, data_count),
                    "quality_score": 60,
                    "attempts": 1,
                    "fallback": True
                }
            
            return {
                "html_content": html_content,
                "quality_score": 85,
                "attempts": 1,
                "fallback": False
            }
            
        except Exception as claude_error:
            debug_log("Claude HTML 생성 오류", str(claude_error))
            return {
                "html_content": create_simple_fallback_html(question, data_count),
                "quality_score": 60,
                "attempts": 1,
                "fallback": True
            }
        
    except Exception as e:
        debug_log("창의적 HTML 생성 전체 오류", str(e))
        print(f"[ERROR] Creative HTML generation error: {traceback.format_exc()}")
        return {
            "html_content": create_simple_fallback_html(question, 0),
            "quality_score": 50,
            "attempts": 1,
            "fallback": True
        }

# API 엔드포인트들

@app.route('/quick', methods=['POST'])
def quick_query():
    """빠른 조회 - 데이터만 반환"""
    debug_log("빠른 조회 시작")
    
    try:
        # 요청 검증
        if not request.json:
            debug_log("요청 JSON 없음")
            return jsonify({
                "success": False,
                "error": "JSON 요청이 필요합니다.",
                "mode": "quick"
            }), 400

        if 'question' not in request.json:
            debug_log("질문 필드 없음")
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다.",
                "mode": "quick"
            }), 400

        question = request.json['question']
        debug_log("질문 수신", question)
        
        if not question or not question.strip():
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다.",
                "mode": "quick"
            }), 400
        
        question = question.strip()
        
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
        
        debug_log("빠른 조회 완료", f"행 수: {query_result.get('row_count', 0)}")
        
        return jsonify({
            "success": True,
            "mode": "quick",
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0)
        })
        
    except Exception as e:
        debug_log("빠른 조회 오류", str(e))
        print(f"[ERROR] Quick query error: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "quick"
        }), 500

@app.route('/creative-html', methods=['POST'])
def creative_html_analysis():
    """창의적 HTML 분석 - 단순화된 버전"""
    debug_log("창의적 HTML 분석 시작")
    
    try:
        # 요청 데이터 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다.",
                "mode": "creative_html"
            }), 400

        question = request.json['question'].strip()
        debug_log("창의적 HTML 질문", question)
        
        if not question:
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다.",
                "mode": "creative_html"
            }), 400
        
        # SQL 생성 및 데이터 조회
        try:
            sql_query = natural_language_to_sql(question)
            debug_log("SQL 생성 완료", sql_query)
        except Exception as e:
            debug_log("SQL 생성 오류", str(e))
            return jsonify({
                "success": False,
                "error": f"SQL 변환 중 오류: {str(e)}",
                "mode": "creative_html",
                "original_question": question
            }), 500
        
        query_result = execute_bigquery(sql_query)
        debug_log("쿼리 실행 결과", f"Success: {query_result['success']}")
        
        if not query_result["success"]:
            return jsonify({
                "success": False,
                "error": query_result["error"],
                "mode": "creative_html",
                "original_question": question,
                "generated_sql": sql_query
            }), 500
        
        # 데이터 검증
        data = query_result.get("data", [])
        debug_log("조회된 데이터", f"Type: {type(data)}, Length: {len(data) if isinstance(data, list) else 'N/A'}")
        
        # HTML 생성
        html_result = generate_creative_html_simple(question, sql_query, data)
        debug_log("HTML 생성 결과", f"Fallback: {html_result.get('fallback', False)}")
        
        return jsonify({
            "success": True,
            "mode": "creative_html",
            "original_question": question,
            "generated_sql": sql_query,
            "row_count": query_result.get("row_count", len(data) if isinstance(data, list) else 0),
            "html_content": html_result["html_content"],
            "quality_score": html_result["quality_score"],
            "attempts": html_result["attempts"],
            "is_fallback": html_result.get("fallback", False)
        })
        
    except Exception as e:
        debug_log("창의적 HTML 분석 오류", str(e))
        print(f"[ERROR] Creative HTML analysis error: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "creative_html"
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
            "bigquery": "configured" if bigquery_client else "not configured"
        },
        "debug_mode": True
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "엔드포인트를 찾을 수 없습니다."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    debug_log("내부 서버 오류", str(error))
    return jsonify({
        "success": False,
        "error": "내부 서버 오류가 발생했습니다."
    }), 500

if __name__ == '__main__':
    print("🚀 디버깅 모드로 서버 시작")
    print(f"프로젝트 ID: {PROJECT_ID}")
    print(f"테이블: {PROJECT_ID}.test_dataset.events_20201121")
    print("지원 모드: 빠른 조회(/quick), 창의적 HTML(/creative-html)")
    
    if not ANTHROPIC_API_KEY:
        print("⚠️  경고: ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    if not bigquery_client:
        print("⚠️  경고: BigQuery 클라이언트가 초기화되지 않았습니다.")
    
    # Cloud Run에서는 PORT 환경변수 사용
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)