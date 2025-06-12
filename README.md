# Automated Billing Retry Pipeline with Lambda, SNS, and SQS

## Table of Contents

- [Overview](#overview)
- [Real-World Business Value](#real-world-business-value)
- [Prerequisites](#prerequisites)
- [Project Folder Structure](#project-folder-structure)
- [Architecture Diagram](#architecture-diagram)
- [How It Works](#how-it-works)
- [Lambda Functions](#lambda-functions)

  - [billing_bucket_parser.py](#billing_bucket_parserpy)
  - [retry_billing_parser.py](#retry_billing_parserpy)

- [IAM Role and Permissions](#iam-role-and-permissions)
- [SNS and SQS Configuration](#sns-and-sqs-configuration)
- [Local Testing](#local-testing)
- [Design Decisions and Highlights](#design-decisions-and-highlights)
- [Errors Encountered](#errors-encountered)
- [Skills Demonstrated](#skills-demonstrated)
- [Conclusion](#conclusion)

---

## Overview

This project is an extension of the [Automated CSV Validation Lambda S3 project](https://github.com/JThomas404/automated-csv-validation-lambda-s3). It introduces a robust error-handling mechanism using an SNS and SQS retry architecture to deal with failures during third-party API calls in the billing validation pipeline.

## Real-World Business Value

- Prevents failed CSV validations from being dropped silently
- Automates retry logic without manual developer intervention
- Keeps stakeholders informed in real-time via SNS email alerts
- Enhances the resilience of ETL pipelines handling financial data

---

## Prerequisites

- Completed setup of the original billing validation pipeline project
- AWS CLI and Terraform configured
- S3 buckets: billing (input), billing-errors (failed), billing-processed (validated)
- Verified email address for SNS notifications
- Python 3.11 virtual environment with `boto3==1.38.35` and `botocore==1.38.35`

---

## Project Folder Structure

```
automated-billing-retry-pipeline-lambda-sns-sqs/
├── lambda/
│   ├── billing_bucket_parser.py
│   ├── retry_billing_parser.py
│   └── event.json
├── README.md
├── requirements.txt
├── s3_files/
│   ├── billing_data_bakery_june_2025.csv
│   ├── billing_data_dairy_june_2025.csv
│   └── billing_data_meat_june_2025.csv
├── scripts/
│   └── package-lambda.sh
└── terraform/
    ├── iam.tf
    ├── lambda.tf
    ├── main.tf
    ├── outputs.tf
    ├── sns.tf
    ├── sqs.tf
    ├── terraform.tfvars
    └── variables.tf
```

---

## Architecture Diagram

```
                   +-----------------------------+
                   |        S3 Billing Bucket     |
                   +-------------+---------------+
                                 |
                                 v
                 +-------------------------------+
                 | BillingBucketParser (Lambda)   |
                 +-------------------------------+
                         |
        +----------------+----------------+
        |                                 |
        v                                 v
+------------------+           +---------------------------+
| Mock 3rd Party   |           |    SNS Topic (Failure)    |
|     API Call     |           +------------+--------------+
+------------------+                        |
                                            v
                                 +--------------------------+
                                 |    SQS Queue (Retry)     |
                                 +------------+-------------+
                                              |
                                              v
                                 +--------------------------+
                                 | RetryBillingParser Lambda|
                                 +-----------+--------------+
                                             |
                            +----------------+----------------+
                            |                                 |
                            v                                 v
                  +------------------+            +-----------------------+
                  | Move to Processed|            | Move to Error Bucket  |
                  |  Bucket          |            |                       |
                  +------------------+            +-----------------------+
```

---

## How It Works

1. The `BillingBucketParser` Lambda is triggered when a new CSV is uploaded to the billing bucket.
2. A mock third-party API call simulates failure. When it fails, the Lambda publishes a message to an SNS topic.
3. The SNS topic fanouts the error message to both an email endpoint and an SQS queue.
4. The message in the queue triggers the `RetryBillingParser` Lambda.
5. The Retry Lambda attempts to re-validate the file and move it to either the processed or error bucket accordingly.

---

## Lambda Functions

### billing_bucket_parser.py

- Added logic to simulate a third-party API failure:

```python
def get_international_taxes(valid_product_lines, billing_bucket, csv_file):
    try:
        raise Exception("API failure: International Taxes API is currently unavailable.")
    except Exception as error:
        sns = boto3.client('sns')
        message = f"Lambda function failed to reach international taxes API for '{billing_bucket}' bucket and file '{csv_file}'."
        sns.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject="Lambda API Call Failure"
        )
        raise error
```

- Existing validation logic updated to ensure that if a file is invalid, it is moved to the error bucket:

```python
if error_found:
    s3.meta.client.copy(copy_source, error_bucket, csv_file)
    s3.Object(billing_bucket, csv_file).delete()
```

### retry_billing_parser.py

- Parses the message body from the SQS event to extract the file path:

```python
message = event['Records'][0]['body']
match = re.search("for '(.*?)' bucket and file '(.*?)'", message)
```

- Re-runs the same validation logic and takes action based on whether errors are found:

```python
if error_found:
    s3.meta.client.copy(copy_source, error_bucket, csv_file)
else:
    s3.meta.client.copy(copy_source, processed_bucket, csv_file)
```

---

## IAM Role and Permissions

```hcl
# Retry Lambda Permissions
sqs:ReceiveMessage
sqs:DeleteMessage

# CloudWatch
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents

# Scoped Resource Access
resource = "arn:aws:sqs:us-east-1:<ACCOUNT_ID>:billing-retry-queue"
```

---

## SNS and SQS Configuration

- `billing-retry-topic`: Receives error notifications from `BillingBucketParser`
- `billing-retry-queue`: Subscribed to the SNS topic
- `RetryBillingParser` Lambda listens to the queue and handles retry logic

---

## Local Testing

### Sample SQS Event

```json
{
  "Records": [
    {
      "body": "Lambda function failed to reach international taxes API for 'boto3-billing-x-da014e82' bucket and file 'billing_data_meats_june_2025.csv'."
    }
  ]
}
```

### Run the Lambda Manually

```python
from retry_billing_parser import lambda_handler

with open("lambda/event.json") as f:
    event = json.load(f)

response = lambda_handler(event, {})
print(response)
```

---

## Design Decisions and Highlights

- Fully asynchronous retry mechanism using SNS → SQS → Lambda
- Environment variables used for all bucket names to enhance reusability
- Code avoids hardcoding sensitive logic or credentials
- Logs meaningful messages to CloudWatch for observability
- IAM permissions tightly scoped using least-privilege principles

---

## Errors Encountered

- **InvalidParameter: Unexpected JSON member: healthyRetryPolicy**

  - Fixed by removing deprecated member from SNS delivery policy

- **SNS Topic Not Found**

  - Resolved by correcting the topic name in `sns.tf`

- **Message not deleting from queue**

  - Resolved by adding `sqs:DeleteMessage` permission

---

## Skills Demonstrated

- Python Lambda development for serverless pipelines
- Event-driven architecture using SNS and SQS
- Fault tolerance and retry logic implementation
- IAM role design with secure permissions
- Terraform-based IaC across all AWS services

---

## Conclusion

This project demonstrates how to enhance serverless validation pipelines by introducing fault-tolerant error handling using AWS Lambda, SNS, and SQS. It ensures reliability, visibility, and reprocessing capability for financial CSV data pipelines. The architecture is modular, scalable, and follows production-ready engineering standards.

---
