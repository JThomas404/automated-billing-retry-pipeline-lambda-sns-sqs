output "sns_topic_arn" {
  description = "ARN of the SNS topic for billing error notifications."
  value       = aws_sns_topic.billing_retry.arn
}

output "billing_lambda_arn" {
  description = "ARN of the main billing Lambda"
  value       = aws_lambda_function.billing_lambda.arn
}

output "retry_billing_lambda_arn" {
  description = "ARN of the retry billing Lambda"
  value       = aws_lambda_function.retry_billing_lambda.arn
}
