import csv
import boto3
import os
from datetime import datetime

# Simulate a third-party API failure for testing purposes
def get_international_taxes(valid_product_lines, billing_bucket, csv_file):
    try:
        raise Exception("API failure: International Taxes API is currently unavailable.")
    except Exception as error:
        sns = boto3.client('sns')
        sns_topic_arn = 'arn:aws:sns:us-east-1:533267010082:billing-retry-topic'
        message = f"Lambda function failed to reach international taxes API for '{billing_bucket}' bucket and file '{csv_file}'."
        sns.publish(
            TopicArn = sns_topic_arn,
            Message = message,
            Subject = "Lambda API Call Failure"
        )
        print("Published failure to sns topic.")
        raise error

def lambda_handler(event, context):
    # Initialise the S3 resource using boto3.
    s3 = boto3.resource('s3')

    # Extract the bucket name and the CSV file name form the 'event' input.
    billing_bucket = event['Records'][0]['s3']['bucket']['name']
    csv_file = event ['Records'][0]['s3']['object']['key']

    # Define the name of the error bucket to copy the erroneous CSV files.
    # Referencing the environment variables created for the S3 buckets in lambda.tf.
    error_bucket = os.environ.get('BILLING_ERROR')

    # Added the name of the processed bucket.
    processed_bucket = os.environ.get('BILLING_PROCESSED')

    # Download the CSV file from S3, read the content, decode from bytes to string, and split the content by lines.
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

    # Initialise a flag (error_found) to false. This flag will be set to true when an error is found.
    error_found = False 

    # Define valid product lines and valid currencies.
    valid_product_lines = ['Bakery', 'Meat', 'Dairy']
    valid_currencies = ['USD', 'MXN', 'CAD']



    # Read the CSV content line by line using the Python's csv reader. Ignore the header line (data[1:]).
    for row in csv.reader(data[1:], delimiter = ','):
        date = row[6]
        product_line = row[4]
        currency = row[7]
        bill_amount = float(row[8])
        # Check if the product line is valid. If not, the error flag will be set to true and will print and error message.
        if product_line not in valid_product_lines:
            error_found = True
            print(f"Error in record {row[0]}: Unrecognised product line: {product_line}.")
            break
        # Check if the currency is valid. If not, the error flag will be set to true and will print and error message.
        if currency not in valid_currencies:
            error_found = True
            print(f"Error in record {row[0]}: Unrecognised currency: {currency}.")
            break
        # Check if the date is in the correct format ('%Y-%m-%d'). If not, the error flag will be set to true and will print and error message.
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            error_found = True
            print(f"Error in record {row[0]}: incorrect date format: {date}.")
            break

    # After parsing all rows, if an error is found, copy the CSV file to the error bucket and delete it from the original bucket.
    if error_found:
        copy_source = {
            'Bucket': billing_bucket,
            'Key': csv_file
        }
        try:
            s3.meta.client.copy(copy_source, error_bucket, csv_file)
            print (f"Moved erroneous file to: {error_bucket}.")
            s3.Object(billing_bucket, csv_file).delete()
            print("Deleted original file from bucket.")
        except Exception as e:
            print (f"Error while moving file: {str(e)}.")

        # Handle any exception that may occur while moving the file, and print the error message.

    # If no errors were found, return a success message with the status code 200 and a body message indicating that no errors were found.
    else:
        copy_source = {
            'Bucket': billing_bucket,
            'Key': csv_file
        }
        try:
            s3.meta.client.copy(copy_source, processed_bucket, csv_file)
            print (f"Moved processes file to: {processed_bucket}.")
            s3.Object(billing_bucket, csv_file).delete()
            print("Deleted original file from bucket.")
        except Exception as e:
            print (f"Error while moving file: {str(e)}.")

