terraform {
  backend "s3" {
    bucket         = "aws-sso-tfstate"                         # S3 버킷 이름
    key            = "iam_identity_center/terraform.tfstate"    # 상태 파일 경로
    region         = "ap-northeast-2"                          # S3 버킷 지역
    dynamodb_table = "TerraformStateLock"                      # DynamoDB 테이블 이름
    encrypt        = true                                      # 상태 파일 암호화
    acl            = "bucket-owner-full-control"
  }
}
