# modules/vpc_endpoints/main.tf

resource "aws_vpc_endpoint" "eks_api" {
  for_each            = var.private_subnet_ids
  service_name        = "com.amazonaws.${var.region}.eks"
  vpc_id              = var.vpc_id
  subnet_ids          = [each.value]
  security_group_ids  = var.security_group_ids
  private_dns_enabled = true
  vpc_endpoint_type   = "Interface"

  tags = merge(
    {
      Name = "eks-api-endpoint-${each.key}"
    },
    var.tags
  )
}

resource "aws_vpc_endpoint" "ecr_api" {
  for_each            = var.private_subnet_ids
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_id              = var.vpc_id
  subnet_ids          = [each.value]
  security_group_ids  = var.security_group_ids
  private_dns_enabled = true
  vpc_endpoint_type   = "Interface"

  tags = merge(
    {
      Name = "ecr-api-endpoint-${each.key}"
    },
    var.tags
  )
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  for_each            = var.private_subnet_ids
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_id              = var.vpc_id
  subnet_ids          = [each.value]
  security_group_ids  = var.security_group_ids
  private_dns_enabled = true
  vpc_endpoint_type   = "Interface"

  tags = merge(
    {
      Name = "ecr-dkr-endpoint-${each.key}"
    },
    var.tags
  )
}
