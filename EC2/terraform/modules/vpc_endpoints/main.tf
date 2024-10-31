resource "aws_vpc_endpoint" "ssm_endpoint" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.ap-northeast-2.ssm"
  vpc_endpoint_type = "Interface"
  subnet_ids        = [var.private_subnet_id]
  security_group_ids = var.security_group_ids

  tags = {
    ManagedBy           = "Terraform"
    ModificationLocked = "true"
  }
}

resource "aws_vpc_endpoint" "ssmmessages_endpoint" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.ap-northeast-2.ssmmessages"
  vpc_endpoint_type = "Interface"
  subnet_ids        = [var.private_subnet_id]
  security_group_ids = var.security_group_ids

  tags = {
    ManagedBy           = "Terraform"
    ModificationLocked = "true"
  }
}

resource "aws_vpc_endpoint" "ec2messages_endpoint" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.ap-northeast-2.ec2messages"
  vpc_endpoint_type = "Interface"
  subnet_ids        = [var.private_subnet_id]
  security_group_ids = var.security_group_ids

  tags = {
    ManagedBy           = "Terraform"
    ModificationLocked = "true"
  }
}
