resource "archive_file" "billing_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/billing_bucket_parser.py"
  output_path = "${path.module}/../lambda/billing_bucket_parser.zip"
}

resource "archive_file" "retry_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/retry_billing_parser.py"
  output_path = "${path.module}/../lambda/retry_billing_parser.zip"
}

resource "aws_lambda_function" "billing_lambda" {
  function_name    = "billing-parser"
  filename         = archive_file.billing_lambda_zip.output_path
  source_code_hash = filebase64sha256(archive_file.billing_lambda_zip.output_path)
  handler          = "billing_bucket_parser.lambda_handler"
  runtime          = "python3.11"
  role             = aws_iam_role.main_billing_lambda_role.arn

  environment {
    variables = {
      BILLING_ERROR     = var.billing_error_bucket
      BILLING_PROCESSED = var.billing_processed_bucket
    }
  }

  tags = var.tags
}

resource "aws_lambda_function" "retry_billing_lambda" {
  function_name    = "retry-billing-parser"
  filename         = archive_file.retry_lambda_zip.output_path
  source_code_hash = filebase64sha256(archive_file.retry_lambda_zip.output_path)
  handler          = "retry_billing_parser.lambda_handler"
  runtime          = "python3.11"
  role             = aws_iam_role.retry_billing_lambda_role.arn

  environment {
    variables = {
      BILLING_ERROR     = var.billing_error_bucket
      BILLING_PROCESSED = var.billing_processed_bucket
    }
  }

  tags = var.tags
}

resource "aws_lambda_permission" "allow_s3_trigger" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.billing_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.billing_source_bucket}"
}

resource "aws_lambda_event_source_mapping" "retry_sqs_trigger" {
  event_source_arn = aws_sqs_queue.billing_retry_queue.arn
  function_name    = aws_lambda_function.retry_billing_lambda.arn
  batch_size       = 1
  enabled          = true
}
