# KMS 키 for DynamoDB 암호화
resource "aws_kms_key" "dynamodb_kms_key" {
  description             = "KMS key for DynamoDB Terraform state lock table encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name      = "DynamoDBStateLockKMSKey"
    ManagedBy = "Terraform"
  }
}

resource "aws_kms_alias" "dynamodb_kms_alias" {
  name          = "alias/dynamodb-state-lock"
  target_key_id = aws_kms_key.dynamodb_kms_key.key_id
}

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

  # KMS를 사용한 서버 측 암호화 활성화
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb_kms_key.arn
  }

  tags = {
    Name      = "Terraform State Lock"
    ManagedBy = "Terraform"
  }
}
