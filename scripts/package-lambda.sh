#!/bin/bash
set -e

cd "$(dirname "$0")/../lambda"

echo "Packaging billing_bucket_parser.py..."
zip billing_bucket_parser.zip billing_bucket_parser.py

echo "Packaging retry_billing_parser.py..."
zip retry_billing_parser.zip retry_billing_parser.py

echo "Packaging complete."
