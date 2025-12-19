# EKS/variables.tf

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

variable "cluster_version" {
  description = "EKS Cluster Version"
  type        = string
  default     = "1.26"
}

variable "ami_release_version" {
  description = "AMI Release Version for EKS Node Groups"
  type        = string
  default     = "auto"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "myproject"
  }
}
