terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}

# US East 1 provider 추가 (CloudFront SSL 인증서용)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# 변수 선언
variable "domain_name" {
  description = "도메인 이름 (S3 버킷 이름으로 사용)"
  type        = string
  default     = "example.com"
}

variable "project_name" {
  description = "프로젝트 이름 (리소스 명명에 사용)"
  type        = string
  default     = "s3-cloudfront-cdn"
}

# S3 버킷 설정
resource "aws_s3_bucket" "cdn_bucket" {
  bucket        = var.domain_name
  force_destroy = true

  tags = {
    Name        = "${var.project_name}-cdn-bucket"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Purpose     = "CDN Static Content"
  }
}

# S3 버킷 버전 관리 활성화 (보안 및 복구를 위해)
resource "aws_s3_bucket_versioning" "cdn_bucket_versioning" {
  bucket = aws_s3_bucket.cdn_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 버킷 수명 주기 정책
resource "aws_s3_bucket_lifecycle_configuration" "cdn_bucket_lifecycle" {
  bucket = aws_s3_bucket.cdn_bucket.id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# S3 버킷 암호화 설정 (KMS 사용 - 보안 강화)
resource "aws_kms_key" "cdn_bucket_kms_key" {
  description             = "KMS key for ${var.project_name} CDN bucket encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project_name}-cdn-bucket-kms-key"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

resource "aws_kms_alias" "cdn_bucket_kms_alias" {
  name          = "alias/${var.project_name}-cdn-bucket"
  target_key_id = aws_kms_key.cdn_bucket_kms_key.key_id
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cdn_bucket_encryption" {
  bucket = aws_s3_bucket.cdn_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.cdn_bucket_kms_key.arn
    }
    bucket_key_enabled = true
  }
}

# S3 버킷 ACL 비활성화 (버킷 소유자만 접근 가능)
resource "aws_s3_bucket_acl" "cdn_bucket_acl" {
  bucket     = aws_s3_bucket.cdn_bucket.id
  acl        = "private"
  depends_on = [aws_s3_bucket_ownership_controls.cdn_bucket_ownership]
}

# S3 버킷 크로스 리전 복제 설정 (선택 사항)
# 주의: 크로스 리전 복제는 추가 비용이 발생하며, 
# DR(Disaster Recovery) 요구사항이 있는 경우에만 활성화하세요.
# 
# 크로스 리전 복제를 활성화하려면:
# 1. 대상 리전의 S3 버킷 생성
# 2. IAM 역할 생성 (복제 권한)
# 3. 아래 주석을 해제하고 설정
#
# resource "aws_s3_bucket_replication_configuration" "cdn_bucket_replication" {
#   role   = aws_iam_role.replication.arn
#   bucket = aws_s3_bucket.cdn_bucket.id
# 
#   rule {
#     id     = "replicate-to-backup-region"
#     status = "Enabled"
# 
#     destination {
#       bucket        = aws_s3_bucket.cdn_bucket_backup.arn
#       storage_class = "STANDARD"
#     }
#   }
# }

resource "aws_s3_bucket_public_access_block" "cdn_bucket_pab" {
  bucket                  = aws_s3_bucket.cdn_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cdn_bucket_ownership" {
  bucket = aws_s3_bucket.cdn_bucket.id
  rule {
    object_ownership = "BucketOwnerEnforced" # ACL 비활성화를 위해 BucketOwnerEnforced 사용
  }
}

# S3 버킷 액세스 로깅 설정 (보안 감사 및 모니터링)
resource "aws_s3_bucket" "cdn_bucket_logs" {
  bucket = "${var.domain_name}-logs"

  tags = {
    Name        = "${var.project_name}-cdn-bucket-logs"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Purpose     = "CDN Bucket Access Logs"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cdn_bucket_logs_encryption" {
  bucket = aws_s3_bucket.cdn_bucket_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_public_access_block" "cdn_bucket_logs_pab" {
  bucket = aws_s3_bucket.cdn_bucket_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "cdn_bucket_logging" {
  bucket = aws_s3_bucket.cdn_bucket.id

  target_bucket = aws_s3_bucket.cdn_bucket_logs.id
  target_prefix = "access-logs/"
}

# S3 버킷 이벤트 알림 설정 (보안 모니터링)
resource "aws_s3_bucket_notification" "cdn_bucket_notification" {
  bucket = aws_s3_bucket.cdn_bucket.id

  # CloudTrail 이벤트는 별도로 설정 필요
  # 여기서는 기본 이벤트 알림만 설정
  depends_on = [aws_s3_bucket.cdn_bucket]
}

resource "aws_s3_bucket_cors_configuration" "cdn_bucket_cors" {
  bucket = aws_s3_bucket.cdn_bucket.id

  cors_rule {
    allowed_headers = ["Authorization", "Content-Type", "X-Requested-With"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = [
      "https://${var.domain_name}",
      "https://*.cloudfront.net"
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 600
  }
}

# WAF Web ACL for CloudFront (Log4j 취약점 방어 포함)
resource "aws_wafv2_web_acl" "cloudfront_waf" {
  name        = "${var.project_name}-cloudfront-waf"
  description = "WAF for CloudFront distribution with Log4j protection"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # AWS 관리형 규칙 세트 - Log4j 취약점 방어 (AMR)
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 1

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # AWS 관리형 규칙 세트 - 일반적인 공격 방어
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rate limiting (DDoS 방어)
  rule {
    name     = "RateLimitRule"
    priority = 10

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-waf-metric"
    sampled_requests_enabled   = true
  }

  tags = {
    Name        = "${var.project_name}-cloudfront-waf"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

# CloudFront 설정
resource "aws_cloudfront_origin_access_control" "cdn_oac" {
  name                              = "${var.project_name}-oac"
  description                       = "OAC for ${var.project_name}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn_distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Static site CDN for ${var.domain_name}"
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.cdn_bucket.bucket_regional_domain_name
    origin_id                = "${var.project_name}-s3-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.cdn_oac.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    web_acl_id             = aws_wafv2_web_acl.cloudfront_waf.arn

    # S3 최적화 캐시 정책
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    # S3의 경우 Origin Request Policy 제거 (호환성 문제)
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
    compress    = true
  }

  ordered_cache_behavior {
    path_pattern           = "*.html"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"

    # HTML 파일은 캐시 비활성화
    cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
    compress    = true
  }

  ordered_cache_behavior {
    path_pattern           = "*.png"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
    compress    = true
  }

  ordered_cache_behavior {
    path_pattern           = "*.svg"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
    compress    = true
  }

  price_class = "PriceClass_200"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.ssl_certificate_validation.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

resource "aws_s3_bucket_policy" "cdn_bucket_policy" {
  bucket = aws_s3_bucket.cdn_bucket.id
  depends_on = [
    aws_cloudfront_distribution.cdn_distribution,
    aws_s3_bucket_public_access_block.cdn_bucket_pab
  ]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          "${aws_s3_bucket.cdn_bucket.arn}",
          "${aws_s3_bucket.cdn_bucket.arn}/*"
        ]
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.cdn_distribution.arn
          }
        }
      }
    ]
  })
}

# CloudFront Response Headers Policy for CORS
resource "aws_cloudfront_response_headers_policy" "cors_policy" {
  name    = "${var.project_name}-cors-policy"
  comment = "CORS policy for ${var.domain_name}"

  cors_config {
    access_control_allow_credentials = false

    access_control_allow_headers {
      items = ["Authorization", "Content-Type", "X-Requested-With"]
    }

    access_control_allow_methods {
      items = ["GET", "HEAD", "OPTIONS"]
    }

    access_control_allow_origins {
      items = [
        "https://${var.domain_name}",
        "https://*.cloudfront.net"
      ]
    }

    access_control_expose_headers {
      items = ["ETag"]
    }

    access_control_max_age_sec = 600
    origin_override            = true
  }

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
  }
}

# SSL 인증서 요청
resource "aws_acm_certificate" "ssl_certificate" {
  provider = aws.us_east_1

  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-ssl-cert"
  }
}

# SSL 인증서 검증을 위한 Route53 레코드 (Cloudflare 사용 시 수동 추가 필요)
resource "aws_acm_certificate_validation" "ssl_certificate_validation" {
  provider = aws.us_east_1

  certificate_arn = aws_acm_certificate.ssl_certificate.arn

  timeouts {
    create = "10m"
  }

  # Cloudflare 사용 시에는 수동으로 DNS 검증 레코드를 추가해야 함
  # 따라서 이 리소스는 무시하고 인증서가 ISSUED 상태가 되면 사용
  depends_on = [aws_acm_certificate.ssl_certificate]
}

# 출력값
output "cloudfront_domain" {
  value       = aws_cloudfront_distribution.cdn_distribution.domain_name
  description = "CloudFront 배포 도메인 이름"
}

output "s3_bucket" {
  value       = aws_s3_bucket.cdn_bucket.bucket
  description = "S3 버킷 이름"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.cdn_distribution.id
  description = "CloudFront 배포 ID"
} 