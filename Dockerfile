# Python 공식 이미지 사용 (slim 버전으로 이미지 크기 최적화)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# 포트 설정 (Cloud Run에서는 PORT 환경변수 사용)
ENV PORT=8080

# 애플리케이션 실행 (production 모드)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app