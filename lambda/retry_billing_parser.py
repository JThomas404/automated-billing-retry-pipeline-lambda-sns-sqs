import csv
import boto3
import os
import re
from datetime import datetime

def lambda_handler(event, context):
    # Initialize the S3 resource using Boto3
    s3 = boto3.resource('s3')

    # Extract the bucket name and CSV file name from the SQS message body
    message = event['Records'][0]['body']
    match = re.search(r"for '(.*?)' bucket and file '(.*?)'", message)
    if match:
        billing_bucket, csv_file = match.groups()
    else:
        print(f"Error parsing message: {message}")
        return {
            'statusCode': 400,
            'body': 'Invalid message format.'
        }

    # Get the destination buckets from environment variables
    error_bucket = os.environ.get('BILLING_ERROR')
    processed_bucket = os.environ.get('BILLING_PROCESSED')

    # Attempt to read and decode the CSV file from S3
    try:
        obj = s3.Object(billing_bucket, csv_file)
        data = obj.get()['Body'].read().decode('utf-8').splitlines()
    except Exception as e:
        print(f"Failed to read or decode file '{csv_file}' from bucket '{billing_bucket}': {str(e)}")
        return {
            'statusCode': 500,
            'body': 'File read or decode failed.'
        }

    if not data:
        print(f"The file '{csv_file}' is empty. Exiting.")
        return {
            'statusCode': 400,
            'body': 'Empty CSV file.'
        }

    # Flag to indicate if validation errors are found
    error_found = False

    # Define valid values for product lines and currencies
    valid_product_lines = ['Bakery', 'Meat', 'Dairy']
    valid_currencies = ['USD', 'MXN', 'CAD']

    # Parse and validate each CSV record (skip header row)
    for row in csv.reader(data[1:], delimiter=','):
        date = row[6]
        product_line = row[4]
        currency = row[7]

        # Validate product line
        if product_line not in valid_product_lines:
            error_found = True
            print(f"Error in record {row[0]}: Unrecognized product line: {product_line}")
            break

        # Validate currency
        if currency not in valid_currencies:
            error_found = True
            print(f"Error in record {row[0]}: Unrecognized currency: {currency}")
            break

        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            error_found = True
            print(f"Error in record {row[0]}: Incorrect date format: {date}")
            break

    # Define copy source
    copy_source = {'Bucket': billing_bucket, 'Key': csv_file}

    # Route the file based on validation outcome
    if error_found:
        try:
            s3.meta.client.copy(copy_source, error_bucket, csv_file)
            print(f"Moved erroneous file to: {error_bucket}")
            s3.Object(billing_bucket, csv_file).delete()
            print("Deleted original file from bucket.")
        except Exception as e:
            print(f"Error while moving file to error bucket: {str(e)}")
    else:
        try:
            s3.meta.client.copy(copy_source, processed_bucket, csv_file)
            print(f"Moved processed file to: {processed_bucket}")
            s3.Object(billing_bucket, csv_file).delete()
            print("Deleted original file from bucket.")
        except Exception as e:
            print(f"Error while moving file to processed bucket: {str(e)}")
