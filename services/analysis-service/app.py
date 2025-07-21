# services/analysis-service/app.py
from flask import Flask, request, jsonify
import anthropic
import os
import json

app = Flask(__name__)

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_data_structure(data):
    """데이터 구조 분석"""
    if not data:
        return {"row_count": 0, "columns": {}}
    
    analysis = {
        "row_count": len(data),
        "columns": {}
    }
    
    for col in data[0].keys():
        values = [row.get(col) for row in data if row.get(col) is not None]
        
        if values:
            first_val = values[0]
            if isinstance(first_val, (int, float)):
                analysis["columns"][col] = {
                    "type": "numeric",
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values)
                }
            else:
                analysis["columns"][col] = {
                    "type": "categorical",
                    "unique_count": len(set(values))
                }
    
    return analysis

def suggest_chart_config(data, columns):
    """차트 설정 제안"""
    if len(columns) == 2:
        col1, col2 = columns[0], columns[1]
        if data and isinstance(data[0].get(col2), (int, float)):
            return {
                "type": "bar",
                "label_column": col1,
                "value_column": col2,
                "title": f"{col1}별 {col2}"
            }
    return None

def generate_analysis_report(question, sql_query, data):
    """구조화된 분석 리포트 생성"""
    data_analysis = analyze_data_structure(data)
    columns = list(data[0].keys()) if data else []
    chart_config = suggest_chart_config(data, columns)
    
    prompt = f"""
    다음 GA4 데이터 분석 결과를 Claude Console 스타일의 리포트로 작성해주세요.
    
    질문: {question}
    데이터 개수: {len(data)}개
    컬럼: {', '.join(columns)}
    
    ## 📊 데이터 분석 리포트 형식으로 작성:
    ### 🎯 핵심 인사이트 (3-4개)
    ### 📈 주요 통계
    ### 💡 비즈니스 시사점
    ### 🚀 다음 단계 제안
    """
    
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return {
        "report": response.content[0].text.strip(),
        "chart_config": chart_config,
        "data_summary": {
            "overview": {
                "total_rows": len(data),
                "columns_count": len(columns)
            },
            "statistics": data_analysis["columns"]
        }
    }

def generate_html_report(question, sql_query, data):
    """HTML 리포트 생성"""
    prompt = f"""
    다음 GA4 분석 결과를 완전한 HTML 페이지로 생성해주세요.
    
    질문: {question}
    데이터: {json.dumps(data[:5], ensure_ascii=False)}
    
    요구사항:
    1. 완전한 HTML 문서 (DOCTYPE부터 </html>까지)
    2. Chart.js 차트 포함
    3. Google 브랜드 컬러 사용
    4. 반응형 디자인
    5. 실제 데이터 기반 인사이트
    
    HTML만 반환해주세요.
    """
    
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    html_content = response.content[0].text.strip()
    
    # HTML 태그 정리
    if html_content.startswith('```html'):
        html_content = html_content.split('```html')[1].split('```')[0].strip()
    
    return {
        "html_content": html_content,
        "quality_score": 85,
        "attempts": 1,
        "fallback": False
    }

@app.route('/structured', methods=['POST'])
def structured_analysis():
    """구조화된 분석"""
    data = request.json
    question = data.get('question')
    sql_query = data.get('sql_query')
    query_data = data.get('data', [])
    
    try:
        result = generate_analysis_report(question, sql_query, query_data)
        
        return jsonify({
            "success": True,
            "mode": "structured",
            "original_question": question,
            "generated_sql": sql_query,
            "data": query_data,
            "row_count": len(query_data),
            "analysis_report": result["report"],
            "chart_config": result["chart_config"],
            "data_summary": result["data_summary"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/creative-html', methods=['POST'])
def creative_html():
    """창의적 HTML 생성"""
    data = request.json
    question = data.get('question')
    sql_query = data.get('sql_query')
    query_data = data.get('data', [])
    
    try:
        result = generate_html_report(question, sql_query, query_data)
        
        return jsonify({
            "success": True,
            "mode": "creative_html",
            "original_question": question,
            "generated_sql": sql_query,
            "row_count": len(query_data),
            "html_content": result["html_content"],
            "quality_score": result["quality_score"],
            "attempts": result["attempts"],
            "is_fallback": result["fallback"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "analysis-service"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)