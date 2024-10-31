output "ssm_endpoint_id" {
  description = "ID of the SSM VPC Endpoint"
  value       = aws_vpc_endpoint.ssm_endpoint.id
}

output "ssmmessages_endpoint_id" {
  description = "ID of the SSMMessages VPC Endpoint"
  value       = aws_vpc_endpoint.ssmmessages_endpoint.id
}

output "ec2messages_endpoint_id" {
  description = "ID of the EC2Messages VPC Endpoint"
  value       = aws_vpc_endpoint.ec2messages_endpoint.id
}
