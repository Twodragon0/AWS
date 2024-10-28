terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.35.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 0.55.0"
    }
  }
}

provider "aws" {
  # No credentials explicitly set here because they come from either the
  # environment or the global credentials file.
  assume_role {
    role_arn = local.workspace_iam_roles[terraform.workspace]
  }
}
