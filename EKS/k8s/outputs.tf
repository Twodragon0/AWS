# k8s/outputs.tf

output "eks_irsa_role_arn" {
  description = "ARN of the EKS IRSA IAM Role"
  value       = aws_iam_role.eks_irsa_role.arn
}

output "kubernetes_service_account_name" {
  description = "Name of the Kubernetes Service Account"
  value       = kubernetes_service_account.example.metadata[0].name
}
