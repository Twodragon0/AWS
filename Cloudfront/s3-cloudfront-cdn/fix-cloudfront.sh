#!/bin/bash

echo "🔧 CloudFront 배포 문제 해결 중..."

# 1. CloudFront 배포 상태 확인
echo "📊 현재 CloudFront 배포 상태:"
aws cloudfront get-distribution --id ? --query 'Distribution.Status' --output text

# 2. 캐시 무효화 상태 확인
echo "🔄 캐시 무효화 상태 확인:"
aws cloudfront list-invalidations --distribution-id ? --query 'InvalidationList.Items[0].{Id:Id,Status:Status}' --output table

# 3. Origin 설정 확인
echo "🌐 Origin 설정 확인:"
aws cloudfront get-distribution --id ? --query 'Distribution.DistributionConfig.Origins.Items[0].{DomainName:DomainName,OriginAccessControlId:OriginAccessControlId}' --output table

# 4. 문제 해결을 위한 Terraform 재적용
echo "🔨 문제가 지속되면 다음 명령어로 CloudFront를 재생성하세요:"
echo "terraform taint aws_cloudfront_distribution.cdn_distribution"


echo ""
echo "📝 테스트 URL: https://*.cloudfront.net/index.html"
echo "⏳ 캐시 무효화가 완료될 때까지 5-15분 기다려주세요." 