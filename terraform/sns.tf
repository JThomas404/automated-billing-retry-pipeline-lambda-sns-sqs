resource "aws_sns_topic" "billing_retry" {
  name = "billing-retry-topic"

  tags = var.tags
}

resource "aws_sns_topic_subscription" "billing_retry_sns_topic" {
  topic_arn = aws_sns_topic.billing_retry.arn
  protocol  = "email"
  endpoint  = "jarredthomas101@gmail.com"

}
