output "lambda_function_arn" {
  description = "ARN of the AWS Monitor Lambda function."
  value       = aws_lambda_function.aws_monitor_lambda.arn
}
