#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# S3 버킷 및 CloudFront 정보
BUCKET_NAME="s3.2twodragon.com"
CLOUDFRONT_ID="EL5VPEVFU1CS3"
CLOUDFRONT_DOMAIN="d4gy2qwg5fhz0.cloudfront.net"

echo -e "${BLUE}🚀 새로운 테스트 페이지 업로드 시작...${NC}"
echo "=================================================="

# 1. S3에 파일 업로드
echo -e "${YELLOW}📁 S3 버킷에 파일 업로드 중...${NC}"
aws s3 sync ./test-content s3://$BUCKET_NAME --delete --exact-timestamps

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 파일 업로드 완료!${NC}"
else
    echo -e "${RED}❌ 파일 업로드 실패!${NC}"
    exit 1
fi

# 2. 업로드된 파일 목록 확인
echo -e "${YELLOW}📋 업로드된 파일 목록:${NC}"
aws s3 ls s3://$BUCKET_NAME --recursive --human-readable

# 3. CloudFront 캐시 무효화
echo -e "${YELLOW}🔄 CloudFront 캐시 무효화 중...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 캐시 무효화 시작됨! ID: $INVALIDATION_ID${NC}"
else
    echo -e "${RED}❌ 캐시 무효화 실패!${NC}"
fi

# 4. 테스트 URL 안내
echo "=================================================="
echo -e "${GREEN}🎉 업로드 완료! 다음 URL에서 테스트하세요:${NC}"
echo ""
echo -e "${BLUE}📍 메인 페이지:${NC}"
echo "   https://$CLOUDFRONT_DOMAIN/"
echo "   https://$CLOUDFRONT_DOMAIN/index.html"
echo ""
echo -e "${BLUE}📍 추가 테스트 페이지:${NC}"
echo "   https://$CLOUDFRONT_DOMAIN/success.html"
echo "   https://$CLOUDFRONT_DOMAIN/error.html"
echo ""
echo -e "${BLUE}🖼️ 이미지 직접 보기:${NC}"
echo "   https://$CLOUDFRONT_DOMAIN/test-image.svg"
echo ""
echo -e "${YELLOW}⏳ 캐시 무효화 완료까지 5-15분 정도 소요됩니다.${NC}"

# 5. 캐시 무효화 상태 확인 (선택사항)
if [ ! -z "$INVALIDATION_ID" ]; then
    echo ""
    echo -e "${BLUE}🔍 캐시 무효화 상태 확인:${NC}"
    aws cloudfront get-invalidation \
        --distribution-id $CLOUDFRONT_ID \
        --id $INVALIDATION_ID \
        --query 'Invalidation.{Id:Id,Status:Status,CreateTime:CreateTime}' \
        --output table
fi

echo ""
echo -e "${GREEN}✨ 모든 작업이 완료되었습니다!${NC}" 