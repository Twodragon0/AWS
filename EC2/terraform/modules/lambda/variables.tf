variable "ec2_sg_id" {
  description = "Security Group ID for EC2 instance"
  type        = string
}

variable "vpc_endpoint_sg_id" {
  description = "Security Group ID for VPC Endpoint"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS Topic ARN for notifications"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket name to store the Excel files"
  type        = string
}
