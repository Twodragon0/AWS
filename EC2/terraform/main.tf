provider "aws" {
  region = "ap-northeast-2"
}

# VPC
resource "aws_vpc" "myproject_prod_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name               = "myproject-prod-vpc"
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${aws_vpc.myproject_prod_vpc.id}/flow-logs"
  retention_in_days = 30

  tags = {
    Name      = "myproject-prod-vpc-flow-logs"
    ManagedBy = "Terraform"
  }
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs_role" {
  name = "vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "vpc-flow-logs-role"
    ManagedBy = "Terraform"
  }
}

resource "aws_iam_role_policy" "vpc_flow_logs_policy" {
  name = "vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# VPC Flow Logs
resource "aws_flow_log" "vpc_flow_logs" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs_role.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.myproject_prod_vpc.id

  tags = {
    Name      = "myproject-prod-vpc-flow-logs"
    ManagedBy = "Terraform"
  }
}

# Default Security Group - 모든 트래픽 차단 (Best Practice)
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.myproject_prod_vpc.id

  ingress = []
  egress  = []

  tags = {
    Name      = "default-sg-restricted"
    ManagedBy = "Terraform"
  }
}

# Public Subnet
resource "aws_subnet" "myproject_prod_public_subnet" {
  vpc_id            = aws_vpc.myproject_prod_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "ap-northeast-2a"

  tags = {
    Name               = "myproject-prod-public-subnet"
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# Private Subnet
resource "aws_subnet" "myproject_prod_private_subnet" {
  vpc_id            = aws_vpc.myproject_prod_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "ap-northeast-2a"

  tags = {
    Name               = "myproject-prod-private-subnet"
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "myproject_prod_igw" {
  vpc_id = aws_vpc.myproject_prod_vpc.id

  tags = {
    Name      = "myproject-prod-igw"
    ManagedBy = "Terraform"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "myproject_prod_nat_gateway" {
  allocation_id = aws_eip.myproject_prod_eip.id
  subnet_id     = aws_subnet.myproject_prod_public_subnet.id

  tags = {
    Name      = "myproject-prod-nat-gateway"
    ManagedBy = "Terraform"
  }
}

# Public Route Table
resource "aws_route_table" "myproject_prod_public_rt" {
  vpc_id = aws_vpc.myproject_prod_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.myproject_prod_igw.id
  }

  tags = {
    Name      = "myproject-prod-public-rt"
    ManagedBy = "Terraform"
  }
}

# Associate Route Table with Public Subnet
resource "aws_route_table_association" "myproject_prod_public_rt_association" {
  subnet_id      = aws_subnet.myproject_prod_public_subnet.id
  route_table_id = aws_route_table.myproject_prod_public_rt.id
}

# IAM Role for SSM Access
resource "aws_iam_role" "myproject_prod_ssm_role" {
  name = "myproject-prod-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# Attach SSM Policy to IAM Role
resource "aws_iam_role_policy_attachment" "myproject_prod_ssm_policy_attachment" {
  role       = aws_iam_role.myproject_prod_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile for EC2
resource "aws_iam_instance_profile" "myproject_prod_ssm_profile" {
  name = "myproject-prod-ssm-instance-profile"
  role = aws_iam_role.myproject_prod_ssm_role.name

  tags = {
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# Security Group for VPC Endpoints (Dedicated for VPC Endpoints)
resource "aws_security_group" "myproject_prod_vpc_endpoint_sg" {
  name        = "myproject-prod-vpc-endpoint-sg"
  description = "Security group for VPC Endpoints"
  vpc_id      = aws_vpc.myproject_prod_vpc.id

  # Ingress rule: Allow only HTTPS traffic for SSM and other services
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # VPC 내 트래픽만 허용
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name               = "myproject-prod-vpc-endpoint-sg"
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# Security Group for EC2 Instance (Allow access only from VPC Endpoints)
resource "aws_security_group" "myproject_prod_ec2_sg" {
  name        = "myproject-prod-ec2-sg"
  description = "Security group for EC2 to allow SSM access"
  vpc_id      = aws_vpc.myproject_prod_vpc.id

  # Ingress rule: Allow HTTPS traffic from the VPC Endpoint's security group
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.myproject_prod_vpc_endpoint_sg.id] # VPC 엔드포인트로부터의 트래픽만 허용
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name               = "myproject-prod-ec2-sg"
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
  }
}

# EC2 Instance in Private Subnet
resource "aws_instance" "myproject_prod_private_instance" {
  ami                         = "ami-01123b84e2a4fba05" # ap-northeast-2의 Amazon Linux 2 AMI
  instance_type               = "t2.micro"
  subnet_id                   = aws_subnet.myproject_prod_private_subnet.id
  associate_public_ip_address = false
  security_groups             = [aws_security_group.myproject_prod_ec2_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.myproject_prod_ssm_profile.name

  # SSM Agent 설치 스크립트
  user_data = <<-EOF
    #!/bin/bash
    yum install -y amazon-ssm-agent
    systemctl enable amazon-ssm-agent
    systemctl start amazon-ssm-agent
  EOF

  tags = {
    Name               = "myproject-prod-private-instance"
    ManagedBy          = "Terraform"
    ModificationLocked = "true"
    Usage              = "prod-name"     # Python 스크립트에서 필터링할 'Usage' 태그 추가
    HostName           = "prod-hostname" # 필요 시 추가
  }
  metadata_options {
    http_tokens = "required"
  }
}

# SNS Topic for Lambda Notifications
resource "aws_sns_topic" "aws_monitor_topic" {
  name = "aws-monitor-topic"

  tags = {
    Name      = "AWS Monitor SNS Topic"
    ManagedBy = "Terraform"
  }
}

# SNS Topic Subscription (이메일 예시)
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.aws_monitor_topic.arn
  protocol  = "email"
  endpoint  = "your-email@example.com" # 실제 이메일 주소로 변경
}

# VPC Endpoints 모듈 호출
module "vpc_endpoints" {
  source             = "./modules/vpc_endpoints"
  vpc_id             = aws_vpc.myproject_prod_vpc.id
  private_subnet_id  = aws_subnet.myproject_prod_private_subnet.id
  security_group_ids = [aws_security_group.myproject_prod_vpc_endpoint_sg.id]
}

# Lambda 모듈 호출
module "lambda" {
  source             = "./modules/lambda"
  ec2_sg_id          = aws_security_group.myproject_prod_ec2_sg.id
  vpc_endpoint_sg_id = aws_security_group.myproject_prod_vpc_endpoint_sg.id
  sns_topic_arn      = aws_sns_topic.aws_monitor_topic.arn
  s3_bucket          = "your-s3-bucket" # 엑셀 파일 저장 S3 버킷 이름
}
