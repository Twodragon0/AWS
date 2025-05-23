# CloudFront SSL 인증서 설정 가이드

## 🔒 **완전한 SSL 인증서 해결 방법**

### 1단계: ACM에서 SSL 인증서 요청

```bash
# us-east-1 리전에서 인증서 생성 (CloudFront 필수)
aws acm request-certificate \
    --domain-name s3.2twodragon.com \
    --validation-method DNS \
    --region us-east-1
```

### 2단계: DNS 검증 레코드 추가

ACM에서 제공하는 DNS 검증 레코드를 Cloudflare에 추가:

| 타입 | 이름 | 값 | 프록시 상태 |
|---|---|---|---|
| CNAME | `_acme-challenge.s3` | AWS 제공 값 | DNS only (회색) |

### 3단계: Terraform에 인증서 추가

```hcl
# main.tf에 추가
data "aws_acm_certificate" "ssl_certificate" {
  domain   = var.domain_name
  statuses = ["ISSUED"]
  
  # CloudFront는 us-east-1 리전 인증서만 사용 가능
  provider = aws.us_east_1
}

# US East 1 provider 추가
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# CloudFront 배포에 인증서 적용
resource "aws_cloudfront_distribution" "cdn_distribution" {
  # ... 기존 설정 ...
  
  aliases = [var.domain_name]
  
  viewer_certificate {
    acm_certificate_arn = data.aws_acm_certificate.ssl_certificate.arn
    ssl_support_method  = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

## 💡 **권장사항**

**방법 1 (Cloudflare Proxy)** 을 권장합니다:
- ✅ 간단하고 빠름
- ✅ Cloudflare가 SSL 자동 처리
- ✅ DDoS 보호 추가
- ✅ 무료

**방법 2 (ACM 인증서)** 는 다음 경우에만:
- AWS에서 모든 것을 관리하고 싶을 때
- Cloudflare를 사용하지 않을 때 