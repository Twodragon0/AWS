output "vpc_id" {
  description = "VPC의 ID"
  value       = aws_vpc.myproject_prod_vpc.id
}

output "private_subnet_id" {
  description = "프라이빗 서브넷의 ID"
  value       = aws_subnet.myproject_prod_private_subnet.id
}

output "ec2_security_group_id" {
  description = "EC2 인스턴스용 보안 그룹 ID"
  value       = aws_security_group.myproject_prod_ec2_sg.id
}

output "vpc_endpoint_sg_id" {
  description = "VPC 엔드포인트용 보안 그룹 ID"
  value       = aws_security_group.myproject_prod_vpc_endpoint_sg.id
}

output "sns_topic_arn" {
  description = "AWS Monitor 알림을 위한 SNS 토픽 ARN"
  value       = aws_sns_topic.aws_monitor_topic.arn
}
