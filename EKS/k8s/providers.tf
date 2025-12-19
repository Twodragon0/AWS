# EKS/k8s/providers.tf

provider "aws" {
  region = var.region
}

# terraform_remote_state를 사용하여 EKS 모듈의 출력값을 참조
data "terraform_remote_state" "infra" {
  backend = "s3"

  config = {
    bucket         = "aws-sso-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "TerraformStateLock"
    encrypt        = true
  }
}


provider "kubernetes" {
  host                   = data.terraform_remote_state.infra.outputs.eks_cluster_endpoint
  cluster_ca_certificate = base64decode(data.terraform_remote_state.infra.outputs.eks_cluster_certificate_authority_data)

  # `aws eks get-token`을 사용하여 토큰 생성
  exec {
    api_version = "client.authentication.k8s.io/v1alpha1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      var.cluster_name,
      "--region",
      var.region
    ]
  }
}
