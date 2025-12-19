# infra/main.tf

# VPC 생성
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    {
      Name = "${var.cluster_name}-vpc"
    },
    var.tags
  )
}

# Default Security Group - 모든 트래픽 차단 (Best Practice)
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id

  ingress = []
  egress  = []

  tags = merge(
    {
      Name = "${var.cluster_name}-default-sg-restricted"
    },
    var.tags
  )
}

# 인터넷 게이트웨이 생성
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name = "${var.cluster_name}-igw"
    },
    var.tags
  )
}

# 퍼블릭 서브넷 A 생성
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true

  tags = merge(
    {
      Name                     = "${var.cluster_name}-public-a"
      "kubernetes.io/role/elb" = "1"
    },
    var.tags
  )
}

# 퍼블릭 서브넷 B 생성
resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.region}c"
  map_public_ip_on_launch = true

  tags = merge(
    {
      Name                     = "${var.cluster_name}-public-b"
      "kubernetes.io/role/elb" = "1"
    },
    var.tags
  )
}

# 프라이빗 서브넷 A 생성
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "${var.region}a"

  tags = merge(
    {
      Name                              = "${var.cluster_name}-private-a"
      "kubernetes.io/role/internal-elb" = "1"
    },
    var.tags
  )
}

# 프라이빗 서브넷 B 생성
resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "${var.region}c"

  tags = merge(
    {
      Name                              = "${var.cluster_name}-private-b"
      "kubernetes.io/role/internal-elb" = "1"
    },
    var.tags
  )
}

# 퍼블릭 라우트 테이블 생성
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = merge(
    {
      Name = "${var.cluster_name}-public-rt"
    },
    var.tags
  )
}

# 퍼블릭 서브넷 A와 퍼블릭 라우트 테이블 연관
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_rt.id
}

# 퍼블릭 서브넷 B와 퍼블릭 라우트 테이블 연관
resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public_rt.id
}

# NAT 게이트웨이용 Elastic IP 생성
resource "aws_eip" "nat_eip" {
  domain = "vpc"

  tags = merge(
    {
      Name = "${var.cluster_name}-nat-eip"
    },
    var.tags
  )
}

resource "aws_eip" "myproject_prod_eip" {
  domain = "vpc" // vpc = true 대신 사용
}

# NAT 게이트웨이 생성
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_a.id

  tags = merge(
    {
      Name = "${var.cluster_name}-nat-gw"
    },
    var.tags
  )
}

# 프라이빗 라우트 테이블 생성
resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }

  tags = merge(
    {
      Name = "${var.cluster_name}-private-rt"
    },
    var.tags
  )
}

# 프라이빗 서브넷 A와 프라이빗 라우트 테이블 연관
resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private_rt.id
}

# 프라이빗 서브넷 B와 프라이빗 라우트 테이블 연관
resource "aws_route_table_association" "private_b" {
  subnet_id      = aws_subnet.private_b.id
  route_table_id = aws_route_table.private_rt.id
}

# 클러스터 보안 그룹 생성
resource "aws_security_group" "eks_cluster_sg" {
  name        = "${var.cluster_name}-cluster-sg"
  description = "Security group for EKS cluster control plane"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # 필요에 따라 소스 범위 제한
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    {
      Name = "${var.cluster_name}-cluster-sg"
    },
    var.tags
  )
}

# VPC 엔드포인트 보안 그룹 생성
resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "${var.cluster_name}-vpc-endpoint-sg"
  description = "Security group for VPC Endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # VPC 내부 트래픽 허용
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    {
      Name = "${var.cluster_name}-vpc-endpoint-sg"
    },
    var.tags
  )
}

# VPC 엔드포인트 모듈 호출
module "vpc_endpoints" {
  source = "./modules/vpc_endpoints"
  vpc_id = aws_vpc.main.id
  private_subnet_ids = {
    a = aws_subnet.private_a.id
    b = aws_subnet.private_b.id
  }
  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  region             = var.region
  tags               = var.tags
}

# EKS 클러스터 생성
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  vpc_id          = aws_vpc.main.id
  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id,
  ]

  tags = var.tags

  cluster_endpoint_public_access  = false # 프라이빗 접근으로 변경
  cluster_endpoint_private_access = true  # 프라이빗 접근 활성화
  enable_irsa                     = true  # IRSA 활성화

  cluster_addons = {
    vpc-cni = {
      before_compute = true
      most_recent    = true
      configuration_values = jsonencode({
        env = {
          ENABLE_POD_ENI                    = "true"
          ENABLE_PREFIX_DELEGATION          = "true"
          POD_SECURITY_GROUP_ENFORCING_MODE = "standard"
        }
        nodeAgent = {
          enablePolicyEventLogs = "true"
        }
        enableNetworkPolicy = "true"
      })
    }
  }

  create_cluster_security_group = false
  create_node_security_group    = false

  # 클러스터 보안 그룹 ID 전달
  cluster_security_group_id = aws_security_group.eks_cluster_sg.id

  eks_managed_node_groups = {
    default = {
      instance_types           = ["t3.micro"]
      min_size                 = 1
      max_size                 = 1
      desired_size             = 1
      force_update_version     = true
      release_version          = var.ami_release_version
      use_name_prefix          = false
      iam_role_name            = "${var.cluster_name}-ng-default"
      iam_role_use_name_prefix = false

      update_config = {
        max_unavailable_percentage = 50
      }

      labels = {
        workshop-default = "yes"
      }
    }
  }
}

# SNS Topic 생성
resource "aws_sns_topic" "monitor_topic" {
  name = "${var.cluster_name}-monitor-topic"

  tags = merge(
    {
      Name = "${var.cluster_name}-monitor-topic"
    },
    var.tags
  )
}

# SNS Topic Subscription (이메일 예제)
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.monitor_topic.arn
  protocol  = "email"
  endpoint  = "your-email@example.com" # 실제 이메일로 교체
}

# IAM Role for SSM Access 생성
resource "aws_iam_role" "ssm_role" {
  name = "${var.cluster_name}-ssm-role"

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

  tags = merge(
    {
      Name = "${var.cluster_name}-ssm-role"
    },
    var.tags
  )
}

# SSM Policy를 IAM Role에 연결
resource "aws_iam_role_policy_attachment" "ssm_policy_attachment" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile 생성
resource "aws_iam_instance_profile" "ssm_profile" {
  name = "${var.cluster_name}-ssm-instance-profile"
  role = aws_iam_role.ssm_role.name

  tags = merge(
    {
      Name = "${var.cluster_name}-ssm-instance-profile"
    },
    var.tags
  )
}

# Kubernetes 서비스 어카운트 생성 및 IRSA 연결
resource "kubernetes_service_account" "example" {
  metadata {
    name      = "example-service-account"
    namespace = "default"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.eks_irsa_role.arn
    }
  }
}

# EKS IRSA Role 생성
resource "aws_iam_role" "eks_irsa_role" {
  name = "${var.cluster_name}-irsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Federated = module.eks.oidc_provider_arn
        },
        Action = "sts:AssumeRoleWithWebIdentity",
        Condition = {
          StringEquals = {
            "${replace(module.eks.oidc_provider, "https://", "")}:sub" = "system:serviceaccount:default:example-service-account"
          }
        }
      }
    ]
  })

  tags = merge(
    {
      Name = "${var.cluster_name}-irsa-role"
    },
    var.tags
  )
}

# IRSA Role에 정책 연결
resource "aws_iam_role_policy" "eks_irsa_policy" {
  name = "${var.cluster_name}-irsa-policy"
  role = aws_iam_role.eks_irsa_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket"
        ],
        Resource = "*"
      }
    ]
  })
}

# 프라이빗 서브넷에 EC2 인스턴스 생성 (예시)
resource "aws_instance" "private_instance" {
  ami                         = "ami-01123b84e2a4fba05" # ap-northeast-2의 Amazon Linux 2 AMI로 확인 필요
  instance_type               = "t3.micro"              # 최소 비용 인스턴스 유형
  subnet_id                   = aws_subnet.private_a.id # 두 개의 프라이빗 서브넷 중 하나 사용
  associate_public_ip_address = false
  security_groups             = [aws_security_group.vpc_endpoint_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ssm_profile.name

  # SSM Agent 설치 스크립트
  user_data = <<-EOF
    #!/bin/bash
    yum install -y amazon-ssm-agent
    systemctl enable amazon-ssm-agent
    systemctl start amazon-ssm-agent
  EOF

  tags = merge(
    {
      Name = "${var.cluster_name}-private-instance"
    },
    var.tags
  )
}

# 데이터 소스 및 Kubernetes provider는 Configuration 2에서 처리
