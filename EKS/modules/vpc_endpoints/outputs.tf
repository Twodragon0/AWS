# modules/vpc_endpoints/outputs.tf

output "eks_api_endpoint_ids" {
  description = "List of EKS API VPC Endpoint IDs"
  value       = [for ep in aws_vpc_endpoint.eks_api : ep.id]
}

output "ecr_api_endpoint_ids" {
  description = "List of ECR API VPC Endpoint IDs"
  value       = [for ep in aws_vpc_endpoint.ecr_api : ep.id]
}

output "ecr_dkr_endpoint_ids" {
  description = "List of ECR DKR VPC Endpoint IDs"
  value       = [for ep in aws_vpc_endpoint.ecr_dkr : ep.id]
}
