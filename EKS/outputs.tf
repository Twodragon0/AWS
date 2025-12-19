# outputs.tf

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public Subnet IDs"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  description = "Private Subnet IDs"
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "eks_cluster_id" {
  description = "EKS Cluster ID"
  value       = module.eks.cluster_id
}

output "eks_cluster_endpoint" {
  description = "EKS Cluster Endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS Cluster Certificate Authority Data"
  value       = module.eks.cluster_certificate_authority_data
}

output "eks_cluster_security_group_id" {
  description = "EKS Cluster Security Group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_managed_node_group_iam_role_arn" {
  description = "IAM Role ARN for EKS Managed Node Group"
  value       = module.eks.eks_managed_node_groups["default"].iam_role_arn
}

output "vpc_endpoints" {
  description = "VPC Endpoint IDs"
  value = concat(
    module.vpc_endpoints.eks_api_endpoint_ids,
    module.vpc_endpoints.ecr_api_endpoint_ids,
    module.vpc_endpoints.ecr_dkr_endpoint_ids
  )
}

output "sns_topic_arn" {
  description = "SNS Topic ARN for Monitoring"
  value       = aws_sns_topic.monitor_topic.arn
}

output "oidc_provider_arn" {
  description = "OIDC Provider ARN"
  value       = module.eks.oidc_provider_arn
}

output "oidc_provider" {
  description = "OIDC Provider URL"
  value       = module.eks.oidc_provider
}
