#!/usr/bin/env python3
"""
Schedule Automatic Backups to AWS S3

This script sets up automatic backups of the trading system to AWS S3 at specified intervals.
It uses a background process to monitor for changes and trigger backups.
"""

import os
import sys
import time
import datetime
import argparse
import subprocess
import hashlib
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("s3_backup_scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

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
    logging.warning("AWS configuration not found. Using default values.")
    # Set default values
    AWS_REGION = None
    S3_BUCKET_NAME = None
    MAX_BACKUPS = 5
    INCLUDE_VENV = False

def get_project_root():
    """Get the root directory of the trading system project"""
    # This script is in tools/backup, so go up two levels
    return Path(__file__).parent.parent.parent

def calculate_project_hash():
    """
    Calculate a hash of the project files to detect changes
    
    Returns:
        A hash string representing the current state of the project
    """
    project_root = get_project_root()
    
    # Use git to get a list of all tracked files
    try:
        git_files = subprocess.check_output(
            ["git", "-C", str(project_root), "ls-files"], 
            text=True
        ).splitlines()
    except subprocess.CalledProcessError:
        logging.error("Failed to get git files. Is this a git repository?")
        return None
    
    # Calculate a hash of the content of all tracked files
    hasher = hashlib.md5()
    
    for file_path in sorted(git_files):
        full_path = project_root / file_path
        if full_path.is_file():
            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
                    hasher.update(content)
            except Exception as e:
                logging.warning(f"Failed to read {file_path}: {e}")
    
    # Also include sensitive files in the hash calculation
    sensitive_files = [".env", "client_secrets.json", "credentials.json"]
    for file_name in sensitive_files:
        file_path = project_root / file_name
        if file_path.is_file():
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    hasher.update(content)
            except Exception as e:
                logging.warning(f"Failed to read {file_name}: {e}")
    
    return hasher.hexdigest()

def run_backup(bucket_name=None, region=None, access_key=None, secret_key=None):
    """Run the backup script"""
    backup_script = Path(__file__).parent / "backup_to_s3.py"
    
    try:
        cmd = [sys.executable, str(backup_script)]
        
        # Add command line arguments if provided
        if bucket_name:
            cmd.extend(["--bucket", bucket_name])
        if region:
            cmd.extend(["--region", region])
        if access_key:
            cmd.extend(["--access-key", access_key])
        if secret_key:
            cmd.extend(["--secret-key", secret_key])
        
        logging.info("Running backup...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Backup completed successfully")
            for line in result.stdout.splitlines():
                if line.strip():  # Only log non-empty lines
                    logging.info(f"  {line}")
        else:
            logging.error("Backup failed")
            logging.error(f"Error: {result.stderr}")
            
        return result.returncode == 0
    
    except Exception as e:
        logging.error(f"Failed to run backup: {e}")
        return False

def monitor_changes(interval_minutes=60, change_detection=True, bucket_name=None, region=None, access_key=None, secret_key=None):
    """
    Monitor the project for changes and run backups
    
    Args:
        interval_minutes: Minimum time between backups in minutes
        change_detection: Whether to only backup when changes are detected
        bucket_name: S3 bucket name
        region: AWS region
        access_key: AWS access key ID
        secret_key: AWS secret access key
    """
    logging.info(f"Starting S3 backup scheduler")
    logging.info(f"  Interval: {interval_minutes} minutes")
    logging.info(f"  Change detection: {'enabled' if change_detection else 'disabled'}")
    logging.info(f"  S3 bucket: {bucket_name or 'Not specified'}")
    logging.info(f"  AWS region: {region or 'Default'}")
    
    last_backup_time = 0
    last_hash = calculate_project_hash() if change_detection else None
    
    try:
        while True:
            current_time = time.time()
            elapsed_minutes = (current_time - last_backup_time) / 60
            
            # Check if enough time has passed since the last backup
            if elapsed_minutes >= interval_minutes:
                run_backup_now = True
                
                # If change detection is enabled, check if the project has changed
                if change_detection:
                    current_hash = calculate_project_hash()
                    if current_hash == last_hash:
                        logging.info("No changes detected, skipping backup")
                        run_backup_now = False
                    else:
                        logging.info("Changes detected, running backup")
                        last_hash = current_hash
                
                if run_backup_now:
                    success = run_backup(bucket_name, region, access_key, secret_key)
                    if success:
                        last_backup_time = time.time()
            
            # Sleep for a while before checking again
            # Use a shorter sleep time to be more responsive to changes
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logging.info("Backup scheduler stopped by user")

def main():
    parser = argparse.ArgumentParser(description='Schedule automatic backups of the trading system to AWS S3')
    parser.add_argument('--interval', type=int, default=60,
                        help='Minimum time between backups in minutes (default: 60)')
    parser.add_argument('--no-change-detection', action='store_true',
                        help='Disable change detection (backup at fixed intervals)')
    parser.add_argument('--daemon', action='store_true',
                        help='Run as a background daemon process')
    parser.add_argument('--bucket', help='S3 bucket name')
    parser.add_argument('--region', help='AWS region (e.g., us-east-1)')
    parser.add_argument('--access-key', help='AWS access key ID')
    parser.add_argument('--secret-key', help='AWS secret access key')
    
    args = parser.parse_args()
    
    # Use command line arguments if provided, otherwise use config values
    bucket_name = args.bucket or S3_BUCKET_NAME
    aws_region = args.region or AWS_REGION
    aws_access_key = args.access_key or AWS_ACCESS_KEY_ID
    aws_secret_key = args.secret_key or AWS_SECRET_ACCESS_KEY
    
    if args.daemon:
        # Fork the process to run in the background
        try:
            pid = os.fork()
            if pid > 0:
                # Exit the parent process
                logging.info(f"S3 backup scheduler started in background (PID: {pid})")
                sys.exit(0)
        except OSError as e:
            logging.error(f"Failed to fork: {e}")
            sys.exit(1)
        
        # Detach from the terminal
        os.setsid()
        
        # Change working directory
        os.chdir('/')
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+') as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
        with open('/dev/null', 'a+') as f:
            os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Start monitoring for changes
    monitor_changes(
        args.interval, 
        not args.no_change_detection,
        bucket_name,
        aws_region,
        aws_access_key,
        aws_secret_key
    )

if __name__ == "__main__":
    main() 