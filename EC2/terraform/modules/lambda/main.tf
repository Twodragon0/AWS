resource "aws_iam_role" "lambda_role" {
  name = "aws_monitor_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name      = "AWS Monitor Lambda Role"
    ManagedBy = "Terraform"
  }
}

# IAM Role에 필요한 정책 첨부
resource "aws_iam_role_policy_attachment" "lambda_ec2_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

# Lambda 함수
resource "aws_lambda_function" "aws_monitor_lambda" {
  filename         = "${path.module}/aws_monitor.zip"
  function_name    = "aws_monitor_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "aws_monitor.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/aws_monitor.zip")
  runtime          = "python3.8"

  environment {
    variables = {
      EC2_SG_ID          = var.ec2_sg_id
      VPC_ENDPOINT_SG_ID = var.vpc_endpoint_sg_id
      SNS_TOPIC_ARN      = var.sns_topic_arn
      S3_BUCKET          = var.s3_bucket
    }
  }

  tags = {
    Name      = "AWS Monitor Lambda"
    ManagedBy = "Terraform"
  }
}

# CloudWatch Event Rule (스케줄 트리거)
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "aws_monitor_schedule"
  schedule_expression = "rate(5 minutes)"  # 모니터링 주기 설정
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "aws_monitor_lambda"
  arn       = aws_lambda_function.aws_monitor_lambda.arn
}

# Lambda 함수가 CloudWatch Events에서 호출될 수 있도록 권한 부여
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.aws_monitor_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}
