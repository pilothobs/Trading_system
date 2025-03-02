#!/usr/bin/env python3
"""
Configure AWS CLI with credentials from aws_config.py

This script sets up AWS CLI configuration using the credentials from aws_config.py.
It creates the necessary config files in the ~/.aws directory.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def configure_aws_cli():
    """Configure AWS CLI with credentials from aws_config.py"""
    try:
        # Import credentials from aws_config.py
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from tools.backup.aws_config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
        
        # Create ~/.aws directory if it doesn't exist
        aws_dir = Path.home() / '.aws'
        aws_dir.mkdir(exist_ok=True)
        
        # Create credentials file
        credentials_file = aws_dir / 'credentials'
        with open(credentials_file, 'w') as f:
            f.write(f"[default]\n")
            f.write(f"aws_access_key_id = {AWS_ACCESS_KEY_ID}\n")
            f.write(f"aws_secret_access_key = {AWS_SECRET_ACCESS_KEY}\n")
        
        # Create config file
        config_file = aws_dir / 'config'
        with open(config_file, 'w') as f:
            f.write(f"[default]\n")
            f.write(f"region = {AWS_REGION}\n")
            f.write(f"output = json\n")
        
        # Set permissions
        os.chmod(credentials_file, 0o600)
        os.chmod(config_file, 0o600)
        
        logging.info(f"AWS CLI configured successfully with credentials from aws_config.py")
        logging.info(f"Credentials file: {credentials_file}")
        logging.info(f"Config file: {config_file}")
        
        return True
    except Exception as e:
        logging.error(f"Error configuring AWS CLI: {str(e)}")
        return False

if __name__ == "__main__":
    configure_aws_cli() 