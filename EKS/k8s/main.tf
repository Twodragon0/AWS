# EKS/k8s/main.tf
terraform {
  backend "s3" {
    bucket         = "aws-sso-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "TerraformStateLock"
    encrypt        = true
  }
}

resource "kubernetes_service_account" "example" {
  metadata {
    name      = "example-service-account"
    namespace = "default"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.eks_irsa_role.arn
    }
  }
}

resource "aws_iam_role" "eks_irsa_role" {
  name = "${var.cluster_name}-irsa-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "${data.terraform_remote_state.infra.outputs.oidc_provider_arn}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${replace(data.terraform_remote_state.infra.outputs.oidc_provider, "https://", "")}:sub": "system:serviceaccount:default:example-service-account"
        }
      }
    }
  ]
}
EOF

  tags = var.tags
}

resource "aws_iam_role_policy" "eks_irsa_policy" {
  name = "${var.cluster_name}-irsa-policy"
  role = aws_iam_role.eks_irsa_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket"
        ],
        Resource = "*"
      }
    ]
  })
}
