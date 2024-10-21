provider "aws" {
  alias  = "ap_northeast"
  region = "ap-northeast-2"
}

# Default tags for all resources
provider "aws" {
  alias = "default_tags"
  default_tags {
    tags = {
      ManagedBy = "Terraform"
    }
  }
}

# Fetch Okta group data and connect to AWS Identity Center group
data "aws_ssoadmin_instances" "main" {}

# Custom Managed Policy for sandbox Service Security
resource "aws_iam_policy" "custom_sandbox_security_policy" {
  name        = "policy_sandbox_security"
  description = "Custom policy for sandbox Service Security"

  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowSSMKMS",
        "Effect": "Allow",
        "Action": [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ],
        "Resource": "arn:aws:kms:ap-northeast-2:xxxxxxxxxxxx:key/xxxxxx"
      }
    ]
  })

  tags = {
    ManagedBy = "Terraform"
  }
}

# Dev Security Permission Set
resource "aws_ssoadmin_permission_set" "dev_security_permission_set" {
  instance_arn = data.aws_ssoadmin_instances.main.arns[0]
  name         = "dev_security_permission_set"
  description  = "Permission Set for Dev Security"

  tags = {
    ManagedBy = "Terraform"
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "dev_security_policy_ec2_registry_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.dev_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_ssoadmin_managed_policy_attachment" "dev_security_policy_ec2_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.dev_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "dev_security_policy_s3_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.dev_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "dev_security_policy_vpc_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.dev_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonVPCReadOnlyAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "dev_security_policy_lambda_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.dev_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess"
}

# Production Security Permission Set
resource "aws_ssoadmin_permission_set" "prd_security_permission_set" {
  instance_arn = data.aws_ssoadmin_instances.main.arns[0]
  name         = "prd_security_permission_set"
  description  = "Permission Set for Production Security"

  tags = {
    ManagedBy = "Terraform"
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "prd_security_policy_ec2_registry_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.prd_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_ssoadmin_managed_policy_attachment" "prd_security_policy_ec2_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.prd_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "prd_security_policy_s3_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.prd_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "prd_security_policy_vpc_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.prd_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonVPCReadOnlyAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "prd_security_policy_lambda_readonly" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.prd_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess"
}

# sandbox Security Permission Set
resource "aws_ssoadmin_permission_set" "sandbox_security_permission_set" {
  instance_arn = data.aws_ssoadmin_instances.main.arns[0]
  name         = "sandbox_security_permission_set"
  description  = "Permission Set for sandbox Security"

  tags = {
    ManagedBy = "Terraform"
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "sandbox_security_policy_ec2_fullaccess" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.sandbox_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "sandbox_security_policy_ssm_fullaccess" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.sandbox_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}

resource "aws_ssoadmin_managed_policy_attachment" "sandbox_security_policy_security_audit" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.sandbox_security_permission_set.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/SecurityAudit"
}

resource "aws_ssoadmin_managed_policy_attachment" "sandbox_security_policy_custom" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.sandbox_security_permission_set.arn
  managed_policy_arn = aws_iam_policy.custom_sandbox_security_policy.arn
}


# Assign permissions to sandbox Group
resource "aws_ssoadmin_account_assignment" "sandbox_group_assignment" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = "arn:aws:sso:::permissionSet/ssoins-xxxxxxxxxxxxxxxx/ps-xxxxxxxxxxxxxxxx"
  principal_id       = "xxxxx" # Okta Group ID (group_sandbox_security)
  principal_type     = "GROUP"
  target_id          = "xxxxxxxxxxxx" # AWS Account ID
  target_type        = "AWS_ACCOUNT"
}

# Assign permissions to Dev Group
resource "aws_ssoadmin_account_assignment" "dev_group_assignment" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = "arn:aws:sso:::permissionSet/ssoins-xxxxxxxxxxxxxxxx/ps-xxxxxxxxxxxxxxxx"
  principal_id       = "xxxx" # Okta Group ID (group_dev_security)
  principal_type     = "GROUP"
  target_id          = "xxxxxxxxxxxx" # AWS Account ID
  target_type        = "AWS_ACCOUNT"
}

# Assign permissions to Prd Group
resource "aws_ssoadmin_account_assignment" "prd_group_assignment" {
  instance_arn       = data.aws_ssoadmin_instances.main.arns[0]
  permission_set_arn = "arn:aws:sso:::permissionSet/ssoins-xxxxxxxxxxxxxxxx/ps-xxxxxxxxxxxxxxxx"
  principal_id       = "xxxxx" # Okta Group ID (group_prd_security)
  principal_type     = "GROUP"
  target_id          = "xxxxxxxxxxxx" # AWS Account ID
  target_type        = "AWS_ACCOUNT"
}
