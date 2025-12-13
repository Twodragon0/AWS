# IAM Identity Center Terraform Configuration

## Overview

This directory contains Terraform configuration for AWS IAM Identity Center (formerly AWS SSO) to manage access for the `c_security` group across multiple AWS accounts.

## Terraform Backend Configuration

This module uses remote state stored in S3 with DynamoDB state locking:

- **S3 Bucket**: `aws-sso-tfstate`
- **State Key**: `iam_identity_center/terraform.tfstate`
- **DynamoDB Table**: `TerraformStateLock`
- **Region**: `ap-northeast-2`

### Backend Resources

The S3 bucket and DynamoDB table are managed separately in:
- `EC2/terraform/initial_setup/` - Contains the Terraform state backend resources

**Important**: Do NOT define `aws_s3_bucket` or `aws_dynamodb_table` resources in this directory. These are shared resources managed centrally.

## Usage

### Prerequisites

1. Ensure the S3 bucket and DynamoDB table exist:
   ```bash
   cd ../../../../EC2/terraform/initial_setup
   terraform init
   terraform apply
   ```

2. Initialize this Terraform configuration:
   ```bash
   cd ControlTower/aws/audit/ap-northeast-2/iam_identity_center
   terraform init
   ```

### Apply Configuration

```bash
terraform plan
terraform apply
```

## Security Best Practices

- Least privilege principle: Permission sets are scoped to specific environments
- Session duration limits: Shorter sessions for administrative access
- Comprehensive tagging: For cost allocation, compliance, and audit trails
- Separation of duties: Different permission sets for prod/dev environments

## State Management

The Terraform state is stored remotely in S3 with the following security features:
- Encryption at rest (AES256)
- Versioning enabled for state file recovery
- DynamoDB state locking to prevent concurrent modifications
- Point-in-time recovery enabled for DynamoDB table
