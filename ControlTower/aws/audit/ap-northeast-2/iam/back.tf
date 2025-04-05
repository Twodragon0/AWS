terraform {
  backend "s3" {
    encrypt        = true
    region         = "ap-northeast-2"
    dynamodb_table = "TerraformStateLock"
    acl            = "bucket-owner-full-control"
    bucket         = "aws-sso-tfstate"
    key            = "/iam/terraform.tfstate"
  }
}
