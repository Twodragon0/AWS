# modules/vpc_endpoints/variables.tf

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Map of private subnet identifiers to subnet IDs"
  type        = map(string)
}

variable "security_group_ids" {
  description = "List of Security Group IDs"
  type        = list(string)
}

variable "region" {
  description = "AWS Region"
  type        = string
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default     = {}
}
