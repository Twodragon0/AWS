# =============================================================================
# Terraform Configuration
# =============================================================================
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0" # Updated to latest stable version
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 0.55.0"
    }
  }

  # ===========================================================================
  # Backend Configuration
  # ===========================================================================
  # State is stored in S3 with DynamoDB for state locking
  # See back.tf for detailed backend configuration
}

# =============================================================================
# AWS Provider Configuration
# =============================================================================
provider "aws" {
  region = var.region

  # ===========================================================================
  # Authentication
  # ===========================================================================
  # Credentials are obtained from:
  # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
  # 2. AWS SSO (aws configure sso)
  # 3. IAM roles (for EC2 instances, ECS tasks, Lambda functions)
  # 4. Shared credentials file (~/.aws/credentials)
  #
  # For cross-account operations, assume_role is used
  # ===========================================================================
  assume_role {
    role_arn = try(
      local.workspace_iam_roles[terraform.workspace],
      "arn:aws:iam::${local.account_id_audit}:role/role_terraform_workspace"
    )

    # Session name for CloudTrail auditing
    session_name = "terraform-iam-identity-center-${terraform.workspace}"

    # External ID for enhanced security (optional)
    # external_id = var.external_id
  }

  # ===========================================================================
  # Default Tags
  # ===========================================================================
  # Tags applied to all resources created by this provider
  default_tags {
    tags = merge(var.common_tags, {
      Module      = "iam-identity-center"
      Workspace   = terraform.workspace
      LastUpdated = timestamp()
    })
  }
}
