variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "private_subnet_id" {
  description = "The ID of the private subnet"
  type        = string
}

variable "security_group_ids" {
  description = "List of Security Group IDs for the VPC Endpoints"
  type        = list(string)
}
