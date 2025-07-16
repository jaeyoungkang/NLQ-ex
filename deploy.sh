#!/bin/bash

# Cloud Run 배포 스크립트
# 사용법: ./deploy.sh YOUR-PROJECT-ID YOUR-ANTHROPIC-API-KEY

set -e

# 색깔 출력을 위한 함수
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 파라미터 체크
if [ $# -ne 2 ]; then
    print_error "사용법: $0 PROJECT-ID ANTHROPIC-API-KEY"
    exit 1
fi

PROJECT_ID=$1
ANTHROPIC_API_KEY=$2
SERVICE_NAME="flask-bigquery-app"
REGION="asia-northeast3"

print_info "Cloud Run 배포를 시작합니다..."
print_info "프로젝트 ID: $PROJECT_ID"
print_info "서비스 이름: $SERVICE_NAME"
print_info "리전: $REGION"

# 1. 프로젝트 설정
print_info "GCP 프로젝트 설정 중..."
gcloud config set project $PROJECT_ID

# 2. 필요한 API 활성화
print_info "필요한 API 활성화 중..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable secretmanager.googleapis.com

# 3. Secret Manager에 API 키 저장
print_info "Secret Manager에 API 키 저장 중..."
if gcloud secrets describe anthropic-api-key > /dev/null 2>&1; then
    print_warning "Secret 'anthropic-api-key'가 이미 존재합니다. 업데이트합니다."
    echo "$ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-api-key --data-file=-
else
    echo "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=-
fi

# 4. 서비스 계정 생성 및 권한 부여
print_info "서비스 계정 생성 중..."
SA_NAME="flask-bigquery-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if gcloud iam service-accounts describe $SA_EMAIL > /dev/null 2>&1; then
    print_warning "서비스 계정 '$SA_EMAIL'이 이미 존재합니다."
else
    gcloud iam service-accounts create $SA_NAME \
        --display-name "Flask BigQuery Service Account"
fi

# 5. BigQuery 권한 부여
print_info "BigQuery 권한 부여 중..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/bigquery.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/bigquery.dataViewer"

# Secret Manager 접근 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

# 6. Cloud Run 서비스 배포
print_info "Cloud Run 서비스 배포 중..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SA_EMAIL \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --memory 512Mi \
    --cpu 1 \
    --concurrency 80 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10

# 7. 배포 결과 확인
print_info "배포 결과 확인 중..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

print_info "배포 완료!"
print_info "서비스 URL: $SERVICE_URL"

# 8. 헬스 체크
print_info "헬스 체크 수행 중..."
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    print_info "✅ 헬스 체크 성공!"
else
    print_warning "⚠️  헬스 체크 실패. 서비스 로그를 확인해주세요."
fi

# 9. 유용한 명령어 출력
print_info "유용한 명령어들:"
echo "  로그 확인: gcloud run services logs read $SERVICE_NAME --region $REGION"
echo "  서비스 상태: gcloud run services describe $SERVICE_NAME --region $REGION"
echo "  API 테스트: curl -X POST $SERVICE_URL/query -H 'Content-Type: application/json' -d '{\"question\": \"사용자 수를 알려주세요\"}'"

print_info "배포가 완료되었습니다! 🎉"