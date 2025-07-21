# config/schema_config.py
"""
BigQuery GA4 테이블 스키마 설정
"""

PROJECT_ID = "nlq-ex"

# GA4 Events 테이블 스키마 정보
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

def get_full_table_name():
    """완전한 테이블 이름 반환"""
    return f"`{PROJECT_ID}.test_dataset.events_20201121`"

def get_schema_prompt():
    """GA4 테이블 스키마 정보를 프롬프트 형태로 변환"""
    full_table_name = get_full_table_name()
    
    schema_text = f"""다음은 BigQuery GA4 이벤트 데이터의 테이블 스키마 정보입니다 (프로젝트: {PROJECT_ID}):

테이블: {full_table_name}
설명: Google Analytics 4 이벤트 데이터 (2020년 11월 21일)

주요 컬럼:
- event_date (STRING): 이벤트 날짜 (YYYYMMDD 형식)
- event_timestamp (INTEGER): 이벤트 타임스탬프 (마이크로초)
- event_name (STRING): 이벤트 이름 (page_view, purchase, add_to_cart, session_start 등)
- event_value_in_usd (FLOAT): 이벤트 값 (USD)
- user_id (STRING): 사용자 ID
- user_pseudo_id (STRING): 익명 사용자 ID

중첩된 구조체:
- device.category (STRING): 기기 카테고리 (mobile, desktop, tablet)
- device.operating_system (STRING): 운영체제 (iOS, Android, Windows 등)
- device.mobile_brand_name (STRING): 모바일 브랜드명
- geo.country (STRING): 국가
- geo.region (STRING): 지역
- geo.city (STRING): 도시
- traffic_source.name (STRING): 트래픽 소스명
- traffic_source.medium (STRING): 매체
- traffic_source.source (STRING): 소스
- app_info.id (STRING): 앱 ID
- platform (STRING): 플랫폼 (WEB, IOS, ANDROID)

이벤트 매개변수 (event_params 배열):
- event_params 배열에서 특정 매개변수 추출 방법:
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_title')
  (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')

전자상거래 정보:
- ecommerce.purchase_revenue (FLOAT): 구매 매출
- ecommerce.purchase_revenue_in_usd (FLOAT): USD 구매 매출

중요한 BigQuery 함수:
- TIMESTAMP_MICROS(event_timestamp): 타임스탬프를 날짜시간으로 변환
- EXTRACT(HOUR FROM TIMESTAMP_MICROS(event_timestamp)): 시간 추출
- PARSE_DATE('%Y%m%d', event_date): 문자열 날짜를 DATE 타입으로 변환

"""
    
    return schema_text