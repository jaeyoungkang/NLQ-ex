from flask import Flask, request, jsonify, send_from_directory
import os
import json
import traceback
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

@app.route('/quick', methods=['POST'])
def quick_query():
    """빠른 조회 - 테스트용 목업 데이터"""
    print("=== 빠른 조회 API 호출됨 ===")
    
    try:
        # 요청 로깅
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data: {request.get_data()}")
        
        # JSON 파싱 테스트
        if not request.json:
            print("ERROR: No JSON in request")
            return jsonify({
                "success": False,
                "error": "JSON 요청이 필요합니다.",
                "mode": "quick"
            }), 400

        print(f"Request JSON: {request.json}")
        
        if 'question' not in request.json:
            print("ERROR: No question field")
            return jsonify({
                "success": False,
                "error": "질문 필드가 없습니다.",
                "mode": "quick"
            }), 400

        question = request.json['question']
        print(f"Question: {question}")
        
        # 목업 데이터 반환
        mock_data = [
            {"event_name": "page_view", "count": 1500},
            {"event_name": "session_start", "count": 800},
            {"event_name": "click", "count": 600}
        ]
        
        response_data = {
            "success": True,
            "mode": "quick",
            "original_question": question,
            "generated_sql": f"SELECT event_name, COUNT(*) as count FROM `nlq-ex.test_dataset.events_20201121` GROUP BY event_name LIMIT 10;",
            "data": mock_data,
            "row_count": len(mock_data)
        }
        
        print(f"Response data: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR in quick_query: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "quick"
        }), 500

@app.route('/analyze', methods=['POST'])
def structured_analysis():
    """구조화된 분석 - 테스트용"""
    print("=== 구조화 분석 API 호출됨 ===")
    
    try:
        print(f"Request method: {request.method}")
        print(f"Request JSON: {request.get_json()}")
        
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "질문이 필요합니다.",
                "mode": "structured"
            }), 400

        question = request.json['question']
        print(f"Question: {question}")
        
        # 목업 데이터
        mock_data = [
            {"category": "mobile", "users": 1200},
            {"category": "desktop", "users": 800},
            {"category": "tablet", "users": 300}
        ]
        
        response_data = {
            "success": True,
            "mode": "structured",
            "original_question": question,
            "generated_sql": "SELECT device.category, COUNT(DISTINCT user_pseudo_id) as users FROM `nlq-ex.test_dataset.events_20201121` GROUP BY device.category;",
            "data": mock_data,
            "row_count": len(mock_data),
            "analysis_report": "## 📊 테스트 분석 리포트\n\n### 🎯 핵심 인사이트\n- 모바일 사용자가 52.2%로 가장 높음\n- 데스크톱 34.8%, 태블릿 13.0%\n\n### 📈 주요 통계\n- 총 사용자: 2,300명\n- 모바일 우세 확인",
            "chart_config": {
                "type": "bar",
                "label_column": "category",
                "value_column": "users",
                "title": "기기별 사용자 분포"
            },
            "data_summary": {
                "overview": {
                    "total_rows": 3,
                    "columns_count": 2,
                    "data_types": {"category": "categorical", "users": "numeric"}
                },
                "quick_insights": ["📱 모바일이 전체의 52%를 차지", "💻 데스크톱은 35% 수준"]
            }
        }
        
        print(f"Returning response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR in structured_analysis: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "structured"
        }), 500

@app.route('/creative-html', methods=['POST'])
def creative_html_analysis():
    """창의적 HTML - 테스트용"""
    print("=== 창의적 HTML API 호출됨 ===")
    
    try:
        if not request.json or 'question' not in request.json:
            return jsonify({
                "success": False,
                "error": "질문이 필요합니다.",
                "mode": "creative_html"
            }), 400

        question = request.json['question']
        print(f"Question: {question}")
        
        # 간단한 HTML 생성
        simple_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{question} - 테스트 리포트</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 12px; 
            padding: 30px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            color: #333;
        }}
        .chart {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            text-align: center;
        }}
        .insight {{ 
            background: #e8f5e8; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 15px 0;
            border-left: 4px solid #34a853;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {question}</h1>
            <p>GA4 데이터 분석 테스트 리포트</p>
        </div>
        
        <div class="chart">
            <h3>📈 데이터 시각화</h3>
            <p>차트가 여기에 표시됩니다.</p>
            <div style="height: 200px; background: #e3f2fd; border-radius: 4px; display: flex; align-items: center; justify-content: center;">
                <span style="color: #1976d2; font-size: 18px;">📊 테스트 차트</span>
            </div>
        </div>
        
        <div class="insight">
            <h3>🎯 핵심 인사이트</h3>
            <ul>
                <li>테스트 데이터로 생성된 리포트입니다</li>
                <li>실제 GA4 데이터 연결 시 정확한 분석이 제공됩니다</li>
                <li>현재는 목업 데이터를 사용하고 있습니다</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p><em>테스트 모드로 실행 중입니다.</em></p>
        </div>
    </div>
</body>
</html>"""
        
        response_data = {
            "success": True,
            "mode": "creative_html",
            "original_question": question,
            "generated_sql": "-- Test SQL Query",
            "row_count": 3,
            "html_content": simple_html,
            "quality_score": 85,
            "attempts": 1,
            "is_fallback": False
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"ERROR in creative_html_analysis: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "success": False,
            "error": f"서버 오류: {str(e)}",
            "mode": "creative_html"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy - test mode",
        "timestamp": datetime.now().isoformat(),
        "mode": "testing",
        "message": "모든 외부 의존성을 제거한 테스트 모드입니다"
    })

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    print(f"404 Error: {error}")
    return jsonify({
        "success": False,
        "error": "페이지를 찾을 수 없습니다."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"500 Error: {error}")
    print(f"Traceback: {traceback.format_exc()}")
    return jsonify({
        "success": False,
        "error": "내부 서버 오류가 발생했습니다.",
        "details": str(error)
    }), 500

# CORS 문제 해결을 위한 헤더 추가
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    print("🧪 테스트 모드로 서버 시작")
    print("📋 모든 외부 의존성(BigQuery, Anthropic) 제거됨")
    print("🎯 목업 데이터로 API 테스트 진행")
    print("=" * 50)
    
    # Cloud Run에서는 PORT 환경변수 사용
    port = int(os.getenv('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)