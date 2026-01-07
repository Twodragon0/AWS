# API Gateway 보안 및 비용 최적화 가이드

이 폴더는 AWS API Gateway를 Terraform으로 구성하여 DevSecOps, FinOps, DevOps 관점에서 보안과 비용을 최적화하는 예시를 제공합니다.

## 📋 목차

- [개요](#개요)
- [주요 특징](#주요-특징)
- [보안 강화 (DevSecOps)](#보안-강화-devsecops)
- [비용 최적화 (FinOps)](#비용-최적화-finops)
- [운영 최적화 (DevOps)](#운영-최적화-devops)
- [사용 방법](#사용-방법)
- [비용 비교](#비용-비교)
- [보안 모범 사례](#보안-모범-사례)

## 🔰 개요

이 모듈은 AWS API Gateway를 보안하고 비용 효율적으로 구성하기 위한 Terraform 예시를 제공합니다.

### 주요 구성 요소

- **HTTP API**: REST API 대비 70% 비용 절감
- **WAF (Web Application Firewall)**: 종합적인 보안 규칙
- **CloudWatch 모니터링**: 실시간 알람 및 로깅
- **JWT 인증**: 토큰 기반 인증 지원
- **API Key**: 선택적 API 키 인증
- **Rate Limiting**: DDoS 방어 및 비용 보호

## ✨ 주요 특징

### DevSecOps 관점

- ✅ AWS WAF 통합 (관리형 규칙 세트, Rate Limiting, IP 필터링)
- ✅ JWT 토큰 기반 인증 지원
- ✅ API Key 인증 (선택적)
- ✅ CloudWatch Logs 암호화 (KMS)
- ✅ CORS 정책 구성
- ✅ Throttling 및 Quota 설정

### FinOps 관점

- ✅ HTTP API 사용 (REST API 대비 70% 비용 절감)
- ✅ Throttling 설정으로 비용 제어
- ✅ Quota 설정으로 사용량 제한
- ✅ CloudWatch Logs 보관 기간 최적화
- ✅ 상세한 비용 태깅

### DevOps 관점

- ✅ 자동 배포 (auto_deploy)
- ✅ 상세한 액세스 로깅
- ✅ CloudWatch 알람 (4xx, 5xx, 지연 시간, WAF 차단)
- ✅ 다중 스테이지 지원 (prod, dev)
- ✅ Infrastructure as Code (Terraform)

## 🛡️ 보안 강화 (DevSecOps)

### WAF 규칙

1. **AWS 관리형 규칙 세트**
   - Common Rule Set: 일반적인 공격 방어
   - SQL Injection Rule Set: SQL 인젝션 방어
   - Known Bad Inputs Rule Set: 알려진 취약점 방어

2. **Rate Limiting**
   - IP 기반 요청 제한
   - DDoS 공격 방어
   - 비용 보호

3. **IP 필터링**
   - 화이트리스트: 허용된 IP 주소
   - 블랙리스트: 차단된 IP 주소

### 인증 및 인가

- **JWT 인증**: 토큰 기반 인증 지원
- **API Key**: 선택적 API 키 인증
- **Usage Plan**: API 사용량 제한 및 모니터링

### 암호화

- **CloudWatch Logs 암호화**: KMS를 통한 로그 암호화
- **HTTPS 강제**: 모든 트래픽 HTTPS 사용

## 💰 비용 최적화 (FinOps)

### HTTP API vs REST API

| 항목 | HTTP API | REST API | 절감율 |
|------|----------|----------|--------|
| API 호출 비용 (100만 건) | $1.00 | $3.50 | 71% |
| 데이터 전송 비용 | 동일 | 동일 | - |
| 캐싱 | 지원 | 지원 | - |

### 비용 절감 전략

1. **HTTP API 사용**
   - REST API 대비 70% 비용 절감
   - 동일한 기능 제공

2. **Throttling 설정**
   - Burst Limit: 5,000 요청/초
   - Rate Limit: 10,000 요청/초
   - 비정상적인 트래픽으로 인한 비용 증가 방지

3. **Quota 설정**
   - 월간 사용량 제한
   - 예상치 못한 비용 증가 방지

4. **CloudWatch Logs 보관 기간**
   - 기본 30일 보관
   - 필요에 따라 조정 가능

### 예상 비용 (월간)

| 항목 | 비용 | 비고 |
|------|------|------|
| API Gateway (HTTP API) | $1.00 | 100만 건 기준 |
| WAF | $5.00 | 기본 요금 |
| CloudWatch Logs | $0.50 | 1GB 기준 |
| 데이터 전송 | 변동 | 사용량에 따라 |
| **총계** | **$6.50+** | 최소 비용 |

## 🔧 운영 최적화 (DevOps)

### 모니터링 및 알람

1. **CloudWatch 알람**
   - 4xx 오류 모니터링
   - 5xx 오류 모니터링
   - 지연 시간 모니터링
   - WAF 차단 요청 모니터링

2. **액세스 로깅**
   - 요청 ID, IP, 시간, 메서드, 경로
   - 상태 코드, 프로토콜, 응답 길이
   - 사용자 에이전트, 오류 정보

3. **상세 메트릭**
   - API 호출 수
   - 지연 시간
   - 오류율
   - WAF 차단 수

### 자동화

- **자동 배포**: Stage 변경 시 자동 배포
- **Infrastructure as Code**: Terraform으로 관리
- **버전 관리**: Git을 통한 변경 이력 추적

## 🚀 사용 방법

### 1. 변수 설정

`terraform.tfvars` 파일을 생성하고 필요한 변수를 설정합니다:

```hcl
project_name = "my-project"
environment  = "prod"
aws_region   = "ap-northeast-2"

lambda_function_arn = "arn:aws:lambda:ap-northeast-2:123456789012:function:my-function"

# CORS 설정
cors_allowed_origins = ["https://example.com"]
cors_allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
cors_allowed_headers = ["Content-Type", "Authorization"]

# WAF 설정
rate_limit = 2000
allowed_ip_addresses = ["1.2.3.4/32"]
blocked_ip_addresses = []

# JWT 인증 (선택적)
enable_jwt_authorizer = true
jwt_audience          = "my-audience"
jwt_issuer            = "https://cognito-idp.ap-northeast-2.amazonaws.com/ap-northeast-2_XXXXXXXXX"

# API Key (선택적)
enable_api_key = false
```

### 2. Terraform 초기화 및 적용

```bash
# Terraform 초기화
terraform init

# 계획 확인
terraform plan

# 적용
terraform apply
```

### 3. 출력 확인

```bash
# API Gateway 엔드포인트 확인
terraform output api_gateway_stage_invoke_url

# API Key 확인 (활성화된 경우)
terraform output api_key_id
```

## 📊 비용 비교

### HTTP API vs REST API (월간 100만 건 기준)

| 항목 | HTTP API | REST API | 절감액 |
|------|----------|----------|--------|
| API 호출 비용 | $1.00 | $3.50 | $2.50 |
| 데이터 전송 | 동일 | 동일 | - |
| **총계** | **$1.00** | **$3.50** | **$2.50 (71%)** |

### 연간 절감액

- 월간 100만 건: $2.50 × 12 = **$30.00/년**
- 월간 1,000만 건: $25.00 × 12 = **$300.00/년**

## 🔒 보안 모범 사례

### 1. WAF 규칙 최적화

- 필요한 규칙만 활성화하여 비용 절감
- Rate Limiting으로 DDoS 공격 방어
- IP 화이트리스트/블랙리스트 활용

### 2. 인증 강화

- JWT 토큰 기반 인증 사용
- API Key는 필요한 경우에만 활성화
- Usage Plan으로 사용량 제한

### 3. 모니터링

- CloudWatch 알람 설정
- 액세스 로그 활성화
- 정기적인 로그 분석

### 4. 암호화

- CloudWatch Logs 암호화 (KMS)
- HTTPS 강제 사용
- 민감한 데이터는 로그에서 제외

## 📁 파일 구조

```
API-Gateway/
├── README.md                              # 이 문서
└── examples/
    └── secure-api-gateway-optimized.tf    # 보안 및 비용 최적화 예시
```

## 🔗 관련 리소스

- [AWS API Gateway 문서](https://docs.aws.amazon.com/apigateway/)
- [AWS WAF 문서](https://docs.aws.amazon.com/waf/)
- [CloudFront 예시](../Cloudfront/examples/secure-cloudfront-optimized.tf)
- [IAM 예시](../IAM/examples/secure-lambda-role.tf)

## ⚠️ 주의사항

1. **비용 모니터링**: CloudWatch를 통해 비용을 정기적으로 모니터링하세요.
2. **Rate Limiting**: 적절한 Rate Limiting을 설정하여 비용을 제어하세요.
3. **로그 보관**: CloudWatch Logs 보관 기간을 적절히 설정하여 비용을 절감하세요.
4. **WAF 규칙**: 필요한 규칙만 활성화하여 비용을 최적화하세요.
5. **JWT 인증**: JWT 인증을 사용하는 경우 올바른 Issuer와 Audience를 설정하세요.

## 📝 변경 이력

- **2024-01**: 초기 버전 작성
  - HTTP API 지원
  - WAF 통합
  - CloudWatch 모니터링
  - JWT 인증 지원

## 📝 관련 블로그 포스트

이 프로젝트와 관련된 블로그 포스트를 참고하세요:

- [클라우드 시큐리티 과정 7기 - 6주차 Cloudflare 및 github 보안](https://twodragon.tistory.com/684)
- [AWS에서 안전한 데이터베이스 접근 게이트웨이 구축하기: NLB + Security Group 완벽 가이드](https://twodragon.tistory.com/696)

더 많은 블로그 포스트는 [Twodragon 블로그](https://twodragon.tistory.com)에서 확인하실 수 있습니다.

## 🤝 기여

이 모듈을 개선하거나 버그를 발견한 경우, 이슈를 생성하거나 Pull Request를 제출해주세요.

