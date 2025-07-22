# utils/html_utils.py
"""
HTML 생성 및 검증 관련 유틸리티 함수들
"""

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