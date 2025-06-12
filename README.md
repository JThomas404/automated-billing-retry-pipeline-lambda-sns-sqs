# Automated Billing Retry Pipeline using Lambda, SNS, and SQS

## Table of Contents

- [Project Overview](#project-overview)
- [Real-World Business Use Case](#real-world-business-use-case)
- [Architecture Summary](#architecture-summary)
- [How It Works](#how-it-works)
- [Key AWS Services Used](#key-aws-services-used)
- [Prerequisites](#prerequisites)
- [Project Folder Structure](#project-folder-structure)

---

## Project Overview

This project extends the work from [automated-csv-validation-lambda-s3](https://github.com/JThomas404/automated-csv-validation-lambda-s3) by introducing a fault-tolerant retry pipeline for billing file processing. The focus is on improving reliability and observability when working with third-party APIs in a serverless context.

When an error occurs during a third-party API call in the `BillingBucketParser` Lambda function, the event is published to an SNS topic. This triggers two parallel actions:

1. An email notification is sent to relevant team members.
2. The message is delivered to an SQS queue that triggers the `RetryBillingParser` Lambda function.

This ensures billing files are retried in a controlled manner and errors are traceable.

---

## Real-World Business Use Case

Billing systems often rely on external APIs to fetch up-to-date tax rates or currency conversion data. Downtime or instability in third-party services can disrupt invoice generation or delay financial reconciliation. By introducing an event-driven retry pipeline, businesses can:

- Reduce manual error tracking
- Improve billing system resilience
- Ensure timely notifications and automated error recovery

This architecture promotes best practices in cloud-native operations.

---

## Architecture Summary

```
        +-------------------+
        | S3 Bucket Upload  |
        +---------+---------+
                  |
                  v
        +-----------------------+
        | BillingBucketParser   |
        |   (Lambda Function)   |
        +----------+------------+
                   | Error (API failure)
                   v
        +--------------------------+
        |        SNS Topic         |
        +-----------+--------------+
                    |
        +-----------+------------+
        |                        |
        v                        v
  Email Notification      SQS Queue (Dead Letter)
                                |
                                v
                +------------------------------+
                | RetryBillingParser (Lambda)   |
                +------------------------------+
```

---

## Key AWS Services Used

- **Amazon S3**: Stores billing CSV files.
- **AWS Lambda**: Handles file validation and retry logic.
- **Amazon SNS**: Publishes error notifications.
- **Amazon SQS**: Acts as a buffer and retry mechanism.
- **IAM**: Secures function execution and service integrations.

---

## Prerequisites

To proceed with this project, ensure the following are completed:

1. The foundational project from [`automated-csv-validation-lambda-s3`](https://github.com/JThomas404/automated-csv-validation-lambda-s3) is cloned and functioning.
2. A Lambda function named `BillingBucketParser` is in place and integrated with your S3 bucket.
3. You have a billing S3 bucket named `dct-billing-processed`.
4. You have basic knowledge of Python, AWS CLI, and Terraform.
5. AWS credentials and IAM permissions to create SQS, SNS, Lambda, and EventBridge resources.

---

## Project Folder Structure

```
automated-billing-retry-pipeline-lambda-sns-sqs/
├── lambda/
│   ├── billing_bucket_parser.py
│   ├── retry_billing_parser.py
│   └── event.json
├── terraform/
│   ├── main.tf
│   ├── sns.tf
│   ├── sqs.tf
│   ├── lambda.tf
│   ├── iam.tf
│   ├── variables.tf
│   └── outputs.tf
├── scripts/
│   └── package-lambda.sh
├── README.md
└── requirements.txt
```

---
