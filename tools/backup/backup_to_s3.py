#!/usr/bin/env python3
"""
Trading System Backup to AWS S3

This script backs up the entire trading system to an AWS S3 bucket.
It can be run manually or scheduled to run periodically.
"""

import os
import sys
import time
import datetime
import shutil
import subprocess
import argparse
import threading
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("s3_backup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Import AWS SDK
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logging.warning("boto3 not installed. AWS S3 backup disabled.")
    logging.warning("Install with: pip install boto3")

# Try to import AWS configuration
try:
    from aws_config import (
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_REGION,
        S3_BUCKET_NAME,
        MAX_BACKUPS,
        INCLUDE_VENV
    )
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("AWS configuration not found. Using command line arguments.")
    # Set default values
    AWS_REGION = None
    S3_BUCKET_NAME = None
    MAX_BACKUPS = 5
    INCLUDE_VENV = False

def get_project_root():
    """Get the root directory of the trading system project"""
    # This script is in tools/backup, so go up two levels
    return Path(__file__).parent.parent.parent

def create_backup_archive(output_dir=None, include_venv=False):
    """
    Create a backup archive of the trading system
    
    Args:
        output_dir: Directory to save the backup archive (default: project root)
        include_venv: Whether to include the virtual environment in the backup
        
    Returns:
        Path to the created backup archive
    """
    project_root = get_project_root()
    
    if output_dir is None:
        output_dir = project_root
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    # Create timestamp for the backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"trading_system_backup_{timestamp}.zip"
    backup_path = output_dir / backup_filename
    
    logging.info(f"Creating backup archive: {backup_path}")
    
    # Determine which directories to exclude
    exclude_dirs = []
    if not include_venv:
        exclude_dirs.append("venv")
    
    # Create the backup archive
    try:
        # Change to the project root directory
        os.chdir(project_root)
        
        # Use git to get a list of all tracked files
        git_files = subprocess.check_output(
            ["git", "ls-files"], 
            text=True
        ).splitlines()
        
        # Also include untracked files except those in excluded directories
        all_files = []
        for root, dirs, files in os.walk("."):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                # Normalize path format
                file_path = file_path.replace("\\", "/")
                if file_path.startswith("./"):
                    file_path = file_path[2:]
                all_files.append(file_path)
        
        # Create a set of all files to include in the backup
        backup_files = set(all_files)
        
        # Ensure sensitive files are included (even if they're in .gitignore)
        sensitive_files = [".env", "client_secrets.json", "credentials.json"]
        for file in sensitive_files:
            if os.path.exists(file):
                logging.info(f"Including sensitive file in backup: {file}")
                backup_files.add(file)
        
        # Create the zip archive
        shutil.make_archive(
            str(backup_path.with_suffix("")),  # Remove .zip extension
            "zip",
            root_dir=project_root,
            base_dir="."
        )
        
        logging.info(f"Backup archive created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logging.error(f"Error creating backup archive: {e}")
        return None

def create_test_backup(output_dir=None):
    """
    Create a smaller test backup with only essential files
    
    Args:
        output_dir: Directory to save the backup archive (default: project root)
        
    Returns:
        Path to the created backup archive
    """
    project_root = get_project_root()
    
    if output_dir is None:
        output_dir = project_root
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    # Create timestamp for the backup filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"trading_system_test_backup_{timestamp}.zip"
    backup_path = output_dir / backup_filename
    
    logging.info(f"Creating test backup archive: {backup_path}")
    
    # Create a temporary directory for the test backup
    temp_dir = Path(output_dir) / f"temp_backup_{timestamp}"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Copy only essential files to the temp directory
        essential_files = [
            ".env",
            ".gitignore",
            "README.md",
            "DEVELOPMENT_NOTES.md",
            "tools/backup/aws_config.py",
            "tools/backup/backup_to_s3.py",
            "tools/backup/schedule_s3_backup.py",
            "tools/backup/README_AWS.md"
        ]
        
        for file_path in essential_files:
            src_path = project_root / file_path
            if src_path.exists():
                # Create parent directories if needed
                dst_path = temp_dir / file_path
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the file
                shutil.copy2(src_path, dst_path)
                logging.info(f"Added to test backup: {file_path}")
        
        # Create the zip archive
        shutil.make_archive(
            str(backup_path.with_suffix("")),  # Remove .zip extension
            "zip",
            root_dir=temp_dir,
            base_dir="."
        )
        
        logging.info(f"Test backup archive created: {backup_path}")
        
        # Clean up the temp directory
        shutil.rmtree(temp_dir)
        
        return backup_path
        
    except Exception as e:
        logging.error(f"Error creating test backup archive: {e}")
        # Clean up the temp directory if it exists
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return None

def upload_to_s3(file_path, bucket_name, aws_region=None, aws_access_key=None, aws_secret_key=None):
    """
    Upload a file to AWS S3
    
    Args:
        file_path: Path to the file to upload
        bucket_name: Name of the S3 bucket to upload to
        aws_region: AWS region (optional, uses default from AWS config if not specified)
        aws_access_key: AWS access key (optional)
        aws_secret_key: AWS secret access key
        
    Returns:
        True if successful, False otherwise
    """
    if not AWS_AVAILABLE:
        logging.error("AWS SDK (boto3) not available. Skipping upload.")
        return False
    
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
        file_size = os.path.getsize(file_path)
        logging.info(f"File size: {file_size / (1024 * 1024):.2f} MB")
        
        # For large files, use multipart upload with progress callback
        if file_size > 100 * 1024 * 1024:  # If file is larger than 100 MB
            logging.info("Using multipart upload for large file")
            
            # Define a progress callback
            class ProgressPercentage:
                def __init__(self, filename):
                    self._filename = filename
                    self._size = float(os.path.getsize(filename))
                    self._seen_so_far = 0
                    self._lock = threading.Lock()
                    self._last_log_time = time.time()
                
                def __call__(self, bytes_amount):
                    with self._lock:
                        self._seen_so_far += bytes_amount
                        percentage = (self._seen_so_far / self._size) * 100
                        
                        # Log progress every 10 seconds or when complete
                        current_time = time.time()
                        if current_time - self._last_log_time > 10 or self._seen_so_far == self._size:
                            logging.info(f"Upload progress: {percentage:.2f}%")
                            self._last_log_time = current_time
            
            # Upload the file with progress tracking
            s3_key = f"trading_system_backups/{file_name}"
            logging.info(f"Starting upload to S3 key: {s3_key}")
            
            try:
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    Callback=ProgressPercentage(str(file_path))
                )
                logging.info(f"Successfully uploaded to S3: {file_name}")
            except Exception as e:
                logging.error(f"Error during multipart upload: {e}")
                return False
        else:
            # For smaller files, use simple upload
            logging.info(f"Uploading {file_name} to S3...")
            s3_key = f"trading_system_backups/{file_name}"
            
            try:
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key
                )
                logging.info(f"Successfully uploaded to S3: {file_name}")
            except Exception as e:
                logging.error(f"Error during upload: {e}")
                return False
        
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

def cleanup_old_backups(backup_dir, max_backups=5):
    """
    Remove old backup archives to save space
    
    Args:
        backup_dir: Directory containing backup archives
        max_backups: Maximum number of backups to keep
    """
    backup_dir = Path(backup_dir)
    backups = list(backup_dir.glob("trading_system_backup_*.zip"))
    
    # Sort backups by modification time (oldest first)
    backups.sort(key=lambda x: x.stat().st_mtime)
    
    # Remove oldest backups if we have more than max_backups
    if len(backups) > max_backups:
        for backup in backups[:-max_backups]:
            logging.info(f"Removing old backup: {backup}")
            backup.unlink()

def main():
    parser = argparse.ArgumentParser(description='Backup trading system to AWS S3')
    parser.add_argument('--output-dir', help='Directory to save the backup archive')
    parser.add_argument('--include-venv', action='store_true', help='Include virtual environment in backup')
    parser.add_argument('--max-backups', type=int, default=MAX_BACKUPS, help='Maximum number of backups to keep')
    parser.add_argument('--no-upload', action='store_true', help='Skip uploading to S3')
    parser.add_argument('--bucket', help='S3 bucket name')
    parser.add_argument('--region', help='AWS region (e.g., us-east-1)')
    parser.add_argument('--access-key', help='AWS access key ID')
    parser.add_argument('--secret-key', help='AWS secret access key')
    parser.add_argument('--test', action='store_true', help='Create a smaller test backup with only essential files')
    
    args = parser.parse_args()
    
    # Use command line arguments if provided, otherwise use config values
    bucket_name = args.bucket or S3_BUCKET_NAME
    aws_region = args.region or AWS_REGION
    include_venv = args.include_venv or INCLUDE_VENV
    max_backups = args.max_backups
    aws_access_key = args.access_key or AWS_ACCESS_KEY_ID
    aws_secret_key = args.secret_key or AWS_SECRET_ACCESS_KEY
    
    # Create the backup archive
    if args.test:
        logging.info("Creating test backup (smaller size)")
        backup_path = create_test_backup(args.output_dir)
    else:
        logging.info("Creating full backup")
        backup_path = create_backup_archive(args.output_dir, include_venv)
    
    if backup_path:
        # Upload to S3
        if not args.no_upload and AWS_AVAILABLE:
            if bucket_name:
                upload_to_s3(
                    backup_path, 
                    bucket_name, 
                    aws_region,
                    aws_access_key,
                    aws_secret_key
                )
            else:
                logging.warning("No S3 bucket specified. Use --bucket or set S3_BUCKET_NAME in aws_config.py")
                logging.info(f"Backup created successfully at: {backup_path}")
                logging.info("To upload to S3, run with: --bucket YOUR_BUCKET_NAME")
        else:
            logging.info(f"Backup created successfully at: {backup_path}")
            
        # Cleanup old backups
        cleanup_old_backups(backup_path.parent, max_backups)
    
if __name__ == "__main__":
    main() 