# ISMS-P 자동화 감사 모듈
# DevSecOps 모범 사례: 자동화된 컴플라이언스 체크, 보안 감사, 비용 모니터링

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Config (컴플라이언스 모니터링)
resource "aws_config_configuration_recorder" "main" {
  name     = "${var.project_name}-config-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

# Config Delivery Channel
resource "aws_config_delivery_channel" "main" {
  name           = "${var.project_name}-config-delivery"
  s3_bucket_name = aws_s3_bucket.config.bucket
  s3_key_prefix  = "config"
  sns_topic_arn  = aws_sns_topic.config.arn

  depends_on = [aws_config_configuration_recorder.main]
}

# Config 규칙: 암호화 필수
resource "aws_config_config_rule" "encrypted_volumes" {
  name = "${var.project_name}-encrypted-volumes"

  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }

  depends_on = [aws_config_configuration_recorder.main]
}

# Security Hub 활성화
resource "aws_securityhub_account" "main" {
  enable_default_standards = true
}

# GuardDuty 활성화
resource "aws_guardduty_detector" "main" {
  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
}

# CloudTrail (감사 로깅)
resource "aws_cloudtrail" "main" {
  name                          = "${var.project_name}-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.bucket
  include_global_service_events  = true
  is_multi_region_trail         = true
  enable_logging                = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn

  event_selector {
    read_write_type                 = "All"
    include_management_events      = true
    exclude_management_event_sources = []
  }

  tags = {
    Name        = "${var.project_name}-cloudtrail"
    Purpose     = "Audit Logging"
    Environment = var.environment
  }
}

# S3 버킷 (Config)
resource "aws_s3_bucket" "config" {
  bucket = "${var.project_name}-${var.environment}-config-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-config-bucket"
    Purpose     = "AWS Config Storage"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "config" {
  bucket = aws_s3_bucket.config.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "config" {
  bucket = aws_s3_bucket.config.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.config.arn
    }
  }
}

# S3 버킷 (CloudTrail)
resource "aws_s3_bucket" "cloudtrail" {
  bucket = "${var.project_name}-${var.environment}-cloudtrail-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-cloudtrail-bucket"
    Purpose     = "CloudTrail Storage"
    Environment = var.environment
  }
}

# KMS 키
resource "aws_kms_key" "config" {
  description             = "KMS key for Config"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_key" "cloudtrail" {
  description             = "KMS key for CloudTrail"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# IAM 역할
resource "aws_iam_role" "config" {
  name = "${var.project_name}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# 변수 및 데이터 소스
variable "project_name" {
  type    = string
  default = "devsecops"
}

variable "environment" {
  type    = string
  default = "dev"
}

data "aws_caller_identity" "current" {}

