# CloudFront "NotFound" 오류 해결 가이드

## 🚨 현재 상황
- **CloudFront 도메인**: `d4gy2qwg5fhz0.cloudfront.net`
- **S3 버킷**: `s3.2twodragon.com`
- **오류**: "NotFoundThe resource you requested does not exist"

## 🔍 문제 원인 분석

### 1. S3 버킷에 파일이 없음 (가장 가능성 높음)
```bash
# 해결방법: 파일 업로드
aws s3 sync ./test-content s3://s3.2twodragon.com
```

### 2. CloudFront 캐시 문제
```bash
# 해결방법: 캐시 무효화
aws cloudfront create-invalidation --distribution-id EL5VPEVFU1CS3 --paths "/*"
```

### 3. Origin Access Control (OAC) 설정 문제
- CloudFront가 S3 버킷에 접근할 수 없는 상태
- S3 버킷 정책이 CloudFront 접근을 허용하지 않음

### 4. S3 버킷 정책 문제
- Terraform이 버킷 정책을 올바르게 적용하지 못했을 가능성

## ✅ 해결 단계

### 단계 1: AWS 자격증명 설정
```bash
aws configure
# 또는
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="ap-northeast-2"
```

### 단계 2: S3에 파일 업로드
```bash
# 스크립트 실행
./upload-files.sh

# 또는 직접 명령어
aws s3 sync ./test-content s3://s3.2twodragon.com
```

### 단계 3: 버킷 정책 확인
```bash
# 현재 버킷 정책 확인
aws s3api get-bucket-policy --bucket s3.2twodragon.com
```

### 단계 4: CloudFront 캐시 무효화
```bash
aws cloudfront create-invalidation --distribution-id EL5VPEVFU1CS3 --paths "/*"
```

### 단계 5: 테스트
```bash
# 브라우저에서 접속
https://d4gy2qwg5fhz0.cloudfront.net/index.html
```

## 🛠️ 추가 진단 명령어

```bash
# S3 버킷 파일 목록 확인
aws s3 ls s3://s3.2twodragon.com --recursive

# CloudFront 배포 상태 확인
aws cloudfront get-distribution --id EL5VPEVFU1CS3

# S3 버킷 정책 확인
aws s3api get-bucket-policy --bucket s3.2twodragon.com

# 버킷 퍼블릭 액세스 차단 상태 확인
aws s3api get-public-access-block --bucket s3.2twodragon.com
```

## 🔄 Terraform으로 문제 해결

만약 위 방법들로 해결되지 않으면:

```bash
# Terraform 상태 확인
terraform show

# 리소스 재생성
terraform taint aws_s3_bucket_policy.cdn_bucket_policy
terraform apply

# 또는 전체 재생성
terraform destroy
terraform apply
```

## 📞 일반적인 해결책 우선순위

1. **파일 업로드** (90% 확률로 이것이 문제)
2. **CloudFront 캐시 무효화**
3. **버킷 정책 재적용**
4. **OAC 설정 확인** 