#!/usr/bin/env python3
"""
Test AWS S3 Upload

This script creates a small test file and uploads it to AWS S3 to verify credentials.
"""

import os
import sys
import time
import logging
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("s3_test_upload.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Try to import AWS configuration
try:
    from aws_config import (
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_REGION,
        S3_BUCKET_NAME
    )
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("AWS configuration not found. Using command line arguments.")
    # Set default values
    AWS_REGION = None
    S3_BUCKET_NAME = None

def create_test_file():
    """Create a small test file"""
    test_file = Path("s3_test_file.txt")
    with open(test_file, "w") as f:
        f.write("This is a test file for AWS S3 upload.\n")
        f.write(f"Created at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    logging.info(f"Created test file: {test_file}")
    return test_file

def upload_to_s3(file_path, bucket_name, aws_region=None, aws_access_key=None, aws_secret_key=None):
    """Upload a file to AWS S3"""
    try:
        logging.info(f"Uploading to AWS S3 bucket: {bucket_name}")
        
        # Create an S3 client
        if aws_access_key and aws_secret_key:
            logging.info("Using provided AWS credentials")
            s3_client = boto3.client(
                's3',
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            # Use credentials from ~/.aws/credentials or environment variables
            logging.info("Using AWS credentials from config or environment")
            s3_client = boto3.client('s3', region_name=aws_region)
        
        # Get the file name from the path
        file_name = os.path.basename(file_path)
        
        # Upload the file
        logging.info(f"Uploading {file_name} to S3...")
        s3_key = f"test/{file_name}"
        
        s3_client.upload_file(
            str(file_path),
            bucket_name,
            s3_key
        )
        
        logging.info(f"Successfully uploaded to S3: {file_name}")
        
        # Get the URL of the uploaded file
        if aws_region:
            s3_url = f"https://s3.{aws_region}.amazonaws.com/{bucket_name}/{s3_key}"
        else:
            s3_url = f"https://s3.amazonaws.com/{bucket_name}/{s3_key}"
            
        logging.info(f"File available at: {s3_url}")
        return True
        
    except ClientError as e:
        logging.error(f"AWS Error uploading to S3: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during S3 upload: {e}")
        logging.exception("Stack trace:")
        return False

def main():
    # Create a test file
    test_file = create_test_file()
    
    # Upload to S3
    if CONFIG_AVAILABLE:
        success = upload_to_s3(
            test_file,
            S3_BUCKET_NAME,
            AWS_REGION,
            AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY
        )
        
        if success:
            logging.info("Test upload successful!")
        else:
            logging.error("Test upload failed.")
    else:
        logging.error("AWS configuration not available. Cannot upload test file.")

if __name__ == "__main__":
    main() 