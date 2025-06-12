resource "aws_sqs_queue" "billing_retry_queue" {
  name                       = "billing-retry-queue"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 345600

  tags = var.tags
}

resource "aws_sqs_queue_policy" "billing_retry_queue_policy" {
  queue_url = aws_sqs_queue.billing_retry_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action   = "sns:Publish"
      Resource = aws_sns_topic.billing_retry.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = aws_sns_topic.billing_retry.arn
        }
      }

    }]
  })
}

resource "aws_sns_topic_subscription" "billing_retry_sqs_subscription" {
  topic_arn = aws_sns_topic.billing_retry.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.billing_retry_queue.arn
}
