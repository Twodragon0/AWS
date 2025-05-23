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
}

resource "aws_s3_bucket_public_access_block" "cdn_bucket_pab" {
  bucket = aws_s3_bucket.cdn_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cdn_bucket_ownership" {
  bucket = aws_s3_bucket.cdn_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
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
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    
    # S3 최적화 캐시 정책
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    # S3의 경우 Origin Request Policy 제거 (호환성 문제)
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id
    
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  ordered_cache_behavior {
    path_pattern     = "*.html"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    
    # HTML 파일은 캐시 비활성화
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id
    
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }

  ordered_cache_behavior {
    path_pattern     = "*.png"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id
    
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  ordered_cache_behavior {
    path_pattern     = "*.svg"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "${var.project_name}-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    response_headers_policy_id = aws_cloudfront_response_headers_policy.cors_policy.id
    
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  price_class = "PriceClass_200"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
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
        Sid       = "AllowCloudFrontServicePrincipal"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = ["s3:GetObject", "s3:ListBucket"]
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
    origin_override = true
  }

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains = true
      preload = true
      override = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override = true
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
  value = aws_cloudfront_distribution.cdn_distribution.domain_name
  description = "CloudFront 배포 도메인 이름"
}

output "s3_bucket" {
  value = aws_s3_bucket.cdn_bucket.bucket
  description = "S3 버킷 이름"
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.cdn_distribution.id
  description = "CloudFront 배포 ID"
} 