variable "aws_region" {
  description = "Default AWS region for the project resources."
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default = {
    Project     = "billing-retry-pipeline"
    Environment = "Dev"
  }
}

variable "billing_error_bucket" {
  description = "Name of the billing error bucket."
  type        = string
}

variable "billing_processed_bucket" {
  description = "Name of the billing processed bucket."
  type        = string
}

variable "billing_source_bucket" {
  description = "Name of the S3 bucket that triggers the billing Lambda"
  type        = string
}
