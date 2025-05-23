# S3 + CloudFront CDN 구성

이 프로젝트는 AWS S3, CloudFront를 사용하여 안전하고 효율적인 정적 웹사이트 호스팅 인프라를 구성합니다.

## 사전 요구사항

- AWS 계정 및 인증 정보
- 도메인 (DNS 관리 가능)
- Terraform 설치

## 구성 요소

- **S3 버킷** (정적 웹사이트 호스팅)
- **CloudFront 배포** (CDN, ap-northeast-2 리전)
- **Origin Access Control (OAC)** (S3 보안 강화)
- **CORS 및 보안 헤더 설정**

## 아키텍처

```
[Client Browser]
       ↓ HTTPS
[CloudFront CDN]
       ↓ Origin Access Control
[S3 Bucket (Private)]
```

## 사용 방법

### 1. 환경 설정

`terraform.tfvars.example` 파일을 `terraform.tfvars`로 복사하고 필요한 값들을 설정합니다:

```bash
cp terraform.tfvars.example terraform.tfvars
```

### 2. 변수 설정

`terraform.tfvars` 파일을 편집하여 도메인 이름을 설정합니다:

```hcl
bucket_name = "your-domain.com"
```

### 3. Terraform 배포

```bash
# Terraform 초기화
terraform init

# 계획 확인
terraform plan

# 리소스 배포
terraform apply
```

### 4. 정적 웹사이트 파일 업로드

S3 버킷에 정적 웹사이트 파일을 업로드합니다:

```bash
# 테스트 콘텐츠 업로드
aws s3 sync ./test-content s3://your-bucket-name

# 또는 실제 웹사이트 파일 업로드
aws s3 sync ./your-website-files s3://your-bucket-name
```

### 5. DNS 설정

CloudFront 배포가 완료되면 DNS 설정을 통해 도메인을 CloudFront 배포에 연결합니다:

1. Terraform 출력에서 CloudFront 도메인 이름 확인:
   ```bash
   terraform output cloudfront_domain_name
   ```

2. DNS 공급자에서 CNAME 레코드 추가:
   - **Type**: CNAME
   - **Name**: www (또는 원하는 서브도메인)
   - **Target**: CloudFront 도메인 이름 (예: d111111abcdef.cloudfront.net)

## 보안 설정

### S3 보안
- **Private Bucket**: S3 버킷은 완전히 비공개로 설정
- **Bucket Policy**: CloudFront OAC만 접근 허용
- **퍼블릭 액세스 차단**: 모든 퍼블릭 액세스 차단

### CloudFront 보안
- **Origin Access Control (OAC)**: S3 직접 접근 차단
- **HTTPS 강제**: HTTP 요청을 HTTPS로 리디렉션
- **보안 헤더**: 
  - `Strict-Transport-Security`: HTTPS 강제
  - `X-Content-Type-Options`: MIME 타입 스니핑 차단
  - `X-Frame-Options`: 클릭재킹 방지
  - `X-XSS-Protection`: XSS 공격 방지

### CORS 설정
- **명시적 도메인**: 특정 도메인만 허용 (와일드카드 금지)
- **최소 권한**: 필요한 메서드와 헤더만 허용
- **적절한 캐시 시간**: Access-Control-Max-Age 600초 설정

## 모니터링 및 로깅

### CloudFront 로깅
- **액세스 로그**: CloudFront 요청 로그 수집
- **실시간 로그**: 실시간 트래픽 모니터링 (옵션)

### CloudWatch 모니터링
- **메트릭**: 요청 수, 오류율, 레이턴시 모니터링
- **알람**: 임계값 초과 시 알림 설정

## 비용 최적화

### 예상 비용 (월 1TB 트래픽 기준)
- **S3 스토리지**: 약 $25.60 (1TB 저장)
- **CloudFront 트래픽**: 약 $116.74 (서울 리전 기준)
- **총 예상 비용**: 약 $142.34/월

### 비용 절약 팁
1. **적절한 캐시 정책**: 긴 TTL로 Origin 요청 최소화
2. **압축 활성화**: Gzip 압축으로 데이터 전송량 감소
3. **Price Class 조정**: 필요한 지역만 선택하여 비용 절약

## 성능 최적화

### 캐시 전략
- **정적 리소스**: 1년 캐시 (CSS, JS, 이미지)
- **HTML 파일**: 1시간 캐시 (콘텐츠 업데이트 고려)
- **API 응답**: 캐시하지 않음 또는 짧은 TTL

### 압축 설정
- **Gzip 압축**: 텍스트 기반 파일 압축 활성화
- **Brotli 압축**: 더 효율적인 압축 알고리즘 (브라우저 지원 시)

## 문제 해결

### 일반적인 문제들

1. **403 Forbidden 오류**
   - S3 버킷 정책 확인
   - OAC 설정 확인
   - CloudFront 배포 상태 확인

2. **CORS 오류**
   - S3 CORS 설정 확인
   - CloudFront Response Headers Policy 확인
   - 브라우저 개발자 도구에서 헤더 확인

3. **캐시 문제**
   - CloudFront 캐시 무효화 실행
   - 적절한 Cache-Control 헤더 설정
   - 버전 쿼리 파라미터 추가

### 유용한 명령어

```bash
# CloudFront 캐시 무효화
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"

# S3 파일 동기화 (캐시 무효화 포함)
aws s3 sync ./your-files s3://your-bucket --delete
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"

# 배포 상태 확인
terraform show
```

## 주의사항

- **배포 시간**: CloudFront 배포 생성에는 최대 15분이 소요될 수 있습니다.
- **전파 시간**: DNS 변경사항이 전파되는데 최대 48시간이 걸릴 수 있습니다.
- **인증서**: HTTPS 사용을 위해 ACM에서 SSL 인증서를 미리 발급받아야 합니다.
- **도메인 검증**: 인증서 발급 시 도메인 소유권 검증이 필요합니다.

## 추가 리소스

- [AWS CloudFront 개발자 가이드](https://docs.aws.amazon.com/cloudfront/)
- [S3 정적 웹사이트 호스팅](https://docs.aws.amazon.com/s3/latest/userguide/WebsiteHosting.html)
- [CORS 구성 가이드](https://docs.aws.amazon.com/s3/latest/userguide/cors.html) 