# =============================================================================
# Terraform State Backend Resources
# =============================================================================
# This module creates the S3 bucket and DynamoDB table required for Terraform
# remote state management with state locking.
#
# Security Best Practices:
# - S3 bucket encryption enabled
# - Versioning enabled for state file recovery
# - Public access blocked
# - DynamoDB point-in-time recovery enabled
# - Comprehensive tagging for cost allocation and compliance
# =============================================================================

resource "aws_s3_bucket" "terraform_state_bucket" {
  bucket = "aws-sso-tfstate"  # 고유한 S3 버킷 이름이어야 합니다.

  # 버킷이 비어있지 않아도 삭제 가능하도록 설정
  # 주의: 이 설정은 버킷 내 모든 객체를 삭제할 수 있게 합니다
  force_destroy = true

  tags = {
    Name        = "TerraformStateBucket"
    ManagedBy   = "Terraform"
    Environment = "Production"
    Purpose     = "Terraform State Storage"
  }
}

# S3 버킷 버전 관리 활성화 (상태 파일 복구를 위해)
resource "aws_s3_bucket_versioning" "terraform_state_bucket_versioning" {
  bucket = aws_s3_bucket.terraform_state_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 버킷 암호화 설정
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state_bucket_encryption" {
  bucket = aws_s3_bucket.terraform_state_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

# S3 버킷 퍼블릭 액세스 차단
resource "aws_s3_bucket_public_access_block" "terraform_state_bucket_pab" {
  bucket = aws_s3_bucket.terraform_state_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets  = true
}

# S3 버킷 수명 주기 정책 (오래된 버전 정리)
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state_bucket_lifecycle" {
  bucket = aws_s3_bucket.terraform_state_bucket.id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# DynamoDB 테이블 - Terraform State Lock
resource "aws_dynamodb_table" "terraform_state_lock" {
  name         = "TerraformStateLock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Point-in-time recovery 활성화 (데이터 복구를 위해)
  point_in_time_recovery {
    enabled = true
  }

  # 서버 측 암호화 활성화
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "Terraform State Lock"
    ManagedBy    = "Terraform"
    Environment  = "Production"
    Purpose      = "Terraform State Locking"
  }
}

