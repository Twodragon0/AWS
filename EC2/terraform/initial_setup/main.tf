resource "aws_s3_bucket" "terraform_state_bucket" {
  bucket = "aws-sso-tfstate"  # 고유한 S3 버킷 이름이어야 합니다.

  tags = {
    Name        = "TerraformStateBucket"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

resource "aws_dynamodb_table" "terraform_state_lock" {
  name         = "TerraformStateLock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "Terraform State Lock"
    ManagedBy = "Terraform"
  }
}
