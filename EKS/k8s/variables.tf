# EKS/k8s/variables.tf

variable "region" {
  description = "AWS Region"
  type        = string
  default     = "ap-northeast-2"
}

variable "cluster_name" {
  description = "EKS Cluster Name"
  type        = string
  default     = "myproject-prod-eks"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {
    Environment = "production"
    Project     = "myproject"
  }
}
