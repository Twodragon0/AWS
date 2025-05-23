#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}🚨 CloudFront 404 오류 해결 중...${NC}"
echo "=========================================="

# 1. Terraform 상태 확인
echo -e "${YELLOW}📊 현재 Terraform 상태 확인...${NC}"
terraform show | grep -E "(bucket|cloudfront|distribution)"

echo ""
echo -e "${YELLOW}🔧 해결 방법 1: Terraform 리소스 재적용${NC}"
echo "terraform apply -auto-approve"

echo ""
echo -e "${YELLOW}🔧 해결 방법 2: CloudFront 배포 재생성${NC}"
echo "terraform taint aws_cloudfront_distribution.cdn_distribution"
echo "terraform apply -auto-approve"

echo ""
echo -e "${YELLOW}🔧 해결 방법 3: S3 버킷 정책 재적용${NC}"
echo "terraform taint aws_s3_bucket_policy.cdn_bucket_policy"
echo "terraform apply -auto-approve"

echo ""
echo -e "${YELLOW}🔧 해결 방법 4: 전체 재생성${NC}"
echo "terraform destroy -auto-approve"
echo "terraform apply -auto-approve"

echo ""
echo -e "${BLUE}📋 문제 원인 체크리스트:${NC}"
echo "1. ✅ S3 버킷 존재: s3.2twodragon.com"
echo "2. ✅ CloudFront 배포 존재: d4gy2qwg5fhz0.cloudfront.net"
echo "3. ❓ S3에 index.html 파일 존재 여부"
echo "4. ❓ CloudFront OAC 설정 정상 여부"
echo "5. ❓ S3 버킷 정책 적용 여부"
echo "6. ❓ CloudFront 캐시 상태"

echo ""
echo -e "${GREEN}💡 권장 해결 순서:${NC}"
echo "1. terraform apply -auto-approve (CORS 설정 적용)"
echo "2. ./upload-new-files.sh (파일 재업로드 + 캐시 무효화)"
echo "3. 15분 대기 후 테스트"
echo "4. 여전히 안 되면 CloudFront 재생성"

echo ""
echo -e "${BLUE}🌐 테스트 URL:${NC}"
echo "https://d4gy2qwg5fhz0.cloudfront.net/"
echo "https://d4gy2qwg5fhz0.cloudfront.net/index.html" 