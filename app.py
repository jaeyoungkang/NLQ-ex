from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from google.cloud import bigquery
import anthropic
import os
import json
import re
from datetime import datetime

# 설정 및 유틸리티 모듈 임포트
from config.schema_config import PROJECT_ID, TABLE_SCHEMA, get_schema_prompt
from config.prompts import (
    get_sql_generation_system_prompt, 
    get_analysis_report_prompt, 
    get_html_generation_prompt
)
from utils.data_utils import (
    safe_json_serialize, 
    suggest_chart_config, 
    analyze_data_structure, 
    generate_summary_insights
)
from utils.html_utils import validate_claude_html, generate_fallback_html

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # 프론트엔드 URL 허용

# 단순한 메모리 기반 저장소 - 최신 조회 결과 1개만 보관
latest_query_results = {
    "data": None,
    "question": None,
    "sql_query": None,
    "timestamp": None,
    "mode": None,
    "row_count": 0
}

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

# BigQuery 클라이언트 초기화 (프로젝트 ID 명시)
try:
    bigquery_client = bigquery.Client(project=PROJECT_ID)
    print(f"BigQuery 프로젝트 ID: {PROJECT_ID}")
    print(f"BigQuery 클라이언트 프로젝트: {bigquery_client.project}")
except Exception as e:
    print(f"BigQuery 클라이언트 초기화 실패: {e}")
    bigquery_client = None

def save_query_result(question, sql_query, data, mode):
    """조회 결과를 메모리에 저장"""
    global latest_query_results
    
    latest_query_results = {
        "data": data,
        "question": question,
        "sql_query": sql_query,
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "row_count": len(data) if data else 0
    }
    
    print(f"조회 결과 저장됨: {question[:50]}... ({len(data) if data else 0}개 행)")

def natural_language_to_sql(question):
    """자연어 질문을 BigQuery SQL로 변환"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    system_prompt = get_sql_generation_system_prompt()

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
        print(f"BigQuery 실행 중 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

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
    
    analysis_prompt = get_analysis_report_prompt(
        question, sql_query, data_analysis, summary_insights, query_results, max_rows_for_analysis
    )

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
        
        analysis_prompt = get_html_generation_prompt(question, sql_query, query_results)

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

def generate_previous_data_analysis(new_question, previous_data, previous_question):
    """이전 조회 결과와 새 질문을 결합하여 분석"""
    if not anthropic_client:
        raise Exception("Anthropic 클라이언트가 초기화되지 않았습니다.")
    
    # 이전 데이터 요약
    data_summary = f"이전 조회 결과 ({len(previous_data)}개 행)"
    if previous_data:
        columns = list(previous_data[0].keys()) if isinstance(previous_data[0], dict) else []
        data_summary += f", 컬럼: {', '.join(columns)}"
    
    analysis_prompt = f"""다음은 이전에 조회한 GA4 데이터와 새로운 질문입니다. 이전 데이터를 분석하여 새 질문에 답변해주세요.

**이전 질문:** {previous_question}

**이전 조회 데이터 ({len(previous_data)}개 행):**
{json.dumps(previous_data[:20], indent=2, ensure_ascii=False, default=str)}

**새로운 질문:** {new_question}

**요청사항:**
1. 이전 데이터를 기반으로 새 질문에 답변하세요.
2. 구체적인 수치와 인사이트를 포함하세요.
3. 추가 SQL 쿼리가 필요한 경우 제안하세요.
4. 비즈니스 관점의 실용적인 분석을 제공하세요.

**분석 형식:**
## 📊 이전 데이터 기반 분석

### 🎯 질문에 대한 답변
(새 질문에 대한 직접적인 답변)

### 📈 핵심 발견사항
(이전 데이터에서 찾은 주요 인사이트)

### 💡 추천 액션
(다음 단계 제안)

### 🔍 추가 분석 제안
(더 깊은 분석을 위한 제안)
"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        raise Exception(f"이전 데이터 분석 중 오류 발생: {str(e)}")

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
        
        # 조회 결과 저장
        save_query_result(question, sql_query, query_result["data"], "quick")
        
        return jsonify({
            "success": True,
            "mode": "quick",
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0),
            "has_previous_data": latest_query_results["data"] is not None
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
        
        # 조회 결과 저장
        save_query_result(question, sql_query, query_result["data"], "structured")
        
        return jsonify({
            "success": True,
            "mode": "structured",
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_result["data"],
            "row_count": query_result.get("row_count", 0),
            "analysis_report": analysis_result["report"],
            "chart_config": analysis_result["chart_config"],
            "data_summary": analysis_result["data_summary"],
            "has_previous_data": latest_query_results["data"] is not None
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
        
        # 조회 결과 저장
        save_query_result(question, sql_query, data, "creative_html")
        
        return jsonify({
            "success": True,
            "mode": "creative_html",
            "original_question": question,
            "generated_sql": sql_query,
            "row_count": query_result.get("row_count", len(data)),
            "html_content": html_result["html_content"],
            "quality_score": html_result["quality_score"],
            "attempts": html_result["attempts"],
            "is_fallback": html_result.get("fallback", False),
            "has_previous_data": latest_query_results["data"] is not None
        })
        
    except Exception as e:
        print(f"창의적 HTML 분석 중 예상치 못한 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "creative_html"
        }), 500

@app.route('/analyze-previous', methods=['POST'])
def analyze_previous_data():
    """이전 조회 결과를 활용한 추가 분석"""
    try:
        # 요청 검증
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "요청 본문에 'question' 필드가 필요합니다.",
                "mode": "analyze_previous"
            }), 400

        new_question = request.json['question'].strip()
        
        if not new_question:
            return jsonify({
                "success": False,
                "error": "질문이 비어있습니다.",
                "mode": "analyze_previous"
            }), 400
        
        # 이전 데이터 확인
        if not latest_query_results["data"]:
            return jsonify({
                "success": False,
                "error": "이전 조회 결과가 없습니다. 먼저 데이터를 조회해주세요.",
                "mode": "analyze_previous"
            }), 400
        
        # 이전 데이터를 활용한 분석 수행
        analysis_result = generate_previous_data_analysis(
            new_question,
            latest_query_results["data"],
            latest_query_results["question"]
        )
        
        return jsonify({
            "success": True,
            "mode": "analyze_previous",
            "new_question": new_question,
            "previous_question": latest_query_results["question"],
            "previous_data_info": {
                "row_count": latest_query_results["row_count"],
                "timestamp": latest_query_results["timestamp"],
                "mode": latest_query_results["mode"]
            },
            "analysis_report": analysis_result,
            "has_previous_data": True
        })
        
    except Exception as e:
        print(f"이전 데이터 분석 중 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "analyze_previous"
        }), 500

@app.route('/previous-data-info', methods=['GET'])
def get_previous_data_info():
    """저장된 이전 데이터 정보 조회"""
    if not latest_query_results["data"]:
        return jsonify({
            "has_data": False,
            "message": "저장된 이전 데이터가 없습니다."
        })
    
    return jsonify({
        "has_data": True,
        "question": latest_query_results["question"],
        "timestamp": latest_query_results["timestamp"],
        "row_count": latest_query_results["row_count"],
        "mode": latest_query_results["mode"],
        "columns": list(latest_query_results["data"][0].keys()) if latest_query_results["data"] else []
    })

# 기존 엔드포인트들 (하위 호환성)
@app.route('/query', methods=['POST'])
def legacy_query():
    """기존 호환성을 위한 엔드포인트 - 구조화된 분석으로 리다이렉트"""
    return structured_analysis()

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    from config.schema_config import get_full_table_name
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "project_id": PROJECT_ID,
        "table": get_full_table_name(),
        "bigquery_client_project": bigquery_client.project if bigquery_client else "Not initialized",
        "services": {
            "anthropic": "configured" if ANTHROPIC_API_KEY else "not configured",
            "bigquery": "configured (using ADC)" if bigquery_client else "not configured"
        },
        "supported_modes": ["quick", "structured", "creative_html", "analyze_previous"],
        "has_previous_data": latest_query_results["data"] is not None,
        "previous_data_info": {
            "row_count": latest_query_results["row_count"],
            "timestamp": latest_query_results["timestamp"]
        } if latest_query_results["data"] else None
    })

@app.route('/schema', methods=['GET'])
def get_schema():
    """테이블 스키마 정보 조회 엔드포인트"""
    from config.schema_config import get_full_table_name
    
    return jsonify({
        "success": True,
        "project_id": PROJECT_ID,
        "table": get_full_table_name(),
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
    
    from config.schema_config import get_full_table_name
    print(f"프로젝트 ID: {PROJECT_ID}")
    print(f"테이블: {get_full_table_name()}")
    print("지원 모드: 빠른 조회(/quick), 구조화된 분석(/analyze), 창의적 HTML(/creative-html), 이전 데이터 분석(/analyze-previous)")
    
    # Cloud Run에서는 PORT 환경변수 사용
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)