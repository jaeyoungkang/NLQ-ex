# services/api-gateway/app.py
from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

# 서비스 URL 설정
QUERY_SERVICE_URL = os.getenv('QUERY_SERVICE_URL', 'http://localhost:8081')
ANALYSIS_SERVICE_URL = os.getenv('ANALYSIS_SERVICE_URL', 'http://localhost:8082')
WEB_UI_URL = os.getenv('WEB_UI_URL', 'http://localhost:3000')

@app.route('/')
def index():
    """메인 페이지로 리다이렉트"""
    return requests.get(f"{WEB_UI_URL}/").content, 200, {'Content-Type': 'text/html'}

@app.route('/api/quick', methods=['POST'])
def quick_query():
    """빠른 조회 - Query Service로 전달"""
    response = requests.post(f"{QUERY_SERVICE_URL}/quick", json=request.json)
    return response.json(), response.status_code

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """구조화 분석 - Query → Analysis 순차 호출"""
    # 1. 데이터 조회
    query_response = requests.post(f"{QUERY_SERVICE_URL}/execute", json=request.json)
    if query_response.status_code != 200:
        return query_response.json(), query_response.status_code
    
    query_data = query_response.json()
    
    # 2. 분석 수행
    analysis_response = requests.post(f"{ANALYSIS_SERVICE_URL}/structured", json={
        'question': request.json['question'],
        'sql_query': query_data['generated_sql'],
        'data': query_data['data']
    })
    
    return analysis_response.json(), analysis_response.status_code

@app.route('/api/creative-html', methods=['POST'])
def creative_html():
    """창의적 HTML - Query → Analysis 순차 호출"""
    # 1. 데이터 조회
    query_response = requests.post(f"{QUERY_SERVICE_URL}/execute", json=request.json)
    if query_response.status_code != 200:
        return query_response.json(), query_response.status_code
    
    query_data = query_response.json()
    
    # 2. HTML 생성
    analysis_response = requests.post(f"{ANALYSIS_SERVICE_URL}/creative-html", json={
        'question': request.json['question'],
        'sql_query': query_data['generated_sql'],
        'data': query_data['data']
    })
    
    return analysis_response.json(), analysis_response.status_code

@app.route('/health')
def health():
    """헬스체크"""
    return jsonify({"status": "healthy", "service": "api-gateway"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)