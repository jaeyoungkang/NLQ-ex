# utils/data_utils.py
"""
데이터 처리 및 분석 유틸리티 함수들
"""

from datetime import datetime

def safe_json_serialize(obj):
    """JSON 직렬화를 안전하게 수행하는 함수"""
    try:
        if isinstance(obj, dict):
            return {str(k): safe_json_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [safe_json_serialize(item) for item in obj]
        elif isinstance(obj, (datetime, )):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        else:
            return str(obj)
    except Exception as e:
        print(f"JSON 직렬화 오류: {e}")
        return str(obj)

def suggest_chart_config(data, columns):
    """데이터 구조를 분석하여 적절한 차트 설정 제안"""
    if not data or len(data) == 0:
        return None
    
    # 컬럼 개수에 따른 차트 타입 결정
    if len(columns) == 1:
        return None  # 단일 컬럼은 차트로 표현하기 어려움
    
    if len(columns) == 2:
        # 2개 컬럼인 경우
        col1, col2 = columns[0], columns[1]
        
        # 첫 번째 값으로 데이터 타입 판단
        first_val1 = data[0][col1] if data[0][col1] is not None else ""
        first_val2 = data[0][col2] if data[0][col2] is not None else 0
        
        # 두 번째 컬럼이 숫자인 경우
        if isinstance(first_val2, (int, float)):
            # 첫 번째 컬럼이 카테고리인 경우
            if isinstance(first_val1, str):
                return {
                    "type": "bar",
                    "label_column": col1,
                    "value_column": col2,
                    "title": f"{col1}별 {col2}"
                }
    
    # 3개 이상 컬럼인 경우 첫 번째는 라벨, 나머지는 값으로 가정
    if len(columns) >= 3:
        label_col = columns[0]
        value_cols = columns[1:]
        
        # 모든 값 컬럼이 숫자인지 확인
        all_numeric = True
        for col in value_cols:
            if data[0][col] is not None and not isinstance(data[0][col], (int, float)):
                all_numeric = False
                break
        
        if all_numeric:
            return {
                "type": "line" if len(value_cols) > 1 else "bar",
                "label_column": label_col,
                "value_columns": value_cols,
                "title": f"{label_col}별 데이터 비교"
            }
    
    return None

def analyze_data_structure(data):
    """데이터 구조를 분석하여 통계 요약 생성"""
    if not data or len(data) == 0:
        return {
            "row_count": 0,
            "columns": {},
            "summary_stats": {},
            "patterns": []
        }
    
    # 데이터 타입 검증
    if not isinstance(data, list):
        print(f"경고: 데이터가 리스트가 아닙니다: {type(data)}")
        return {
            "row_count": 0,
            "columns": {},
            "summary_stats": {},
            "patterns": ["데이터 타입 오류"]
        }
    
    # 첫 번째 행 검증
    if not data or not isinstance(data[0], dict):
        print(f"경고: 첫 번째 행이 딕셔너리가 아닙니다: {type(data[0]) if data else 'None'}")
        return {
            "row_count": len(data),
            "columns": {},
            "summary_stats": {},
            "patterns": ["데이터 구조 오류"]
        }
    
    analysis = {
        "row_count": len(data),
        "columns": {},
        "summary_stats": {},
        "patterns": []
    }
    
    # 각 컬럼별 분석
    try:
        for col in data[0].keys():
            # 안전한 값 추출
            values = []
            for row in data:
                if isinstance(row, dict) and col in row:
                    val = row[col]
                    if val is not None:
                        values.append(val)
            
            non_null_count = len(values)
            null_count = len(data) - non_null_count
            
            col_analysis = {
                "type": "unknown",
                "non_null_count": non_null_count,
                "null_count": null_count,
                "null_percentage": round((null_count / len(data)) * 100, 1) if len(data) > 0 else 0
            }
            
            if values:
                # 데이터 타입 판단
                first_val = values[0]
                if isinstance(first_val, (int, float)):
                    col_analysis["type"] = "numeric"
                    try:
                        numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                        if numeric_values:
                            col_analysis.update({
                                "min": min(numeric_values),
                                "max": max(numeric_values),
                                "mean": round(sum(numeric_values) / len(numeric_values), 2),
                                "median": round(sorted(numeric_values)[len(numeric_values)//2], 2),
                                "sum": sum(numeric_values)
                            })
                    except Exception as e:
                        print(f"숫자 분석 중 오류: {e}")
                        
                elif isinstance(first_val, str):
                    col_analysis["type"] = "categorical"
                    try:
                        unique_values = list(set(values))
                        col_analysis.update({
                            "unique_count": len(unique_values),
                            "most_common": max(set(values), key=values.count) if values else None,
                            "top_values": dict(sorted(
                                [(v, values.count(v)) for v in set(values[:100])], # 성능을 위해 상위 100개만 처리
                                key=lambda x: x[1], reverse=True
                            )[:5])
                        })
                    except Exception as e:
                        print(f"카테고리 분석 중 오류: {e}")
                        col_analysis["unique_count"] = len(set(str(v) for v in values[:100]))
            
            analysis["columns"][col] = col_analysis
            
    except Exception as e:
        print(f"데이터 구조 분석 중 오류: {e}")
        analysis["patterns"].append(f"분석 중 오류 발생: {str(e)}")
    
    return analysis

def generate_summary_insights(data_analysis, question):
    """데이터 분석 결과를 기반으로 핵심 인사이트 생성"""
    insights = []
    
    # 데이터 크기 인사이트
    row_count = data_analysis["row_count"]
    if row_count > 1000:
        insights.append(f"📊 **대용량 데이터셋**: {row_count:,}개의 레코드로 구성된 상당한 규모의 데이터입니다.")
    elif row_count < 10:
        insights.append(f"📊 **소규모 데이터셋**: {row_count}개의 레코드로 제한적인 샘플입니다.")
    
    # 컬럼별 인사이트
    for col, stats in data_analysis["columns"].items():
        if stats["type"] == "numeric":
            if "sum" in stats and stats["sum"] > 0:
                insights.append(f"🔢 **{col}**: 총합 {stats['sum']:,}, 평균 {stats['mean']:,}, 범위 {stats['min']:,}~{stats['max']:,}")
        elif stats["type"] == "categorical":
            if stats["unique_count"] < row_count * 0.5:  # 중복이 많은 경우
                top_value = list(stats["top_values"].items())[0] if stats["top_values"] else None
                if top_value:
                    percentage = round((top_value[1] / row_count) * 100, 1)
                    insights.append(f"📈 **{col}**: '{top_value[0]}'이 {percentage}%로 가장 높은 비중을 차지합니다.")
    
    return insights