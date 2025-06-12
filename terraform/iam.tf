data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "retry_billing_lambda_role" {
  name               = "retry_billing_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json

  tags = var.tags
}

data "aws_iam_policy_document" "retry_billing_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage"
    ]
    resources = [
      aws_sqs_queue.billing_retry_queue.arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "retry_billing_lambda_policy" {
  name   = "retry_billing_lambda_policy"
  role   = aws_iam_role.retry_billing_lambda_role.id
  policy = data.aws_iam_policy_document.retry_billing_permissions.json
}
