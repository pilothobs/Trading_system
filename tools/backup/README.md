# AWS S3 Backup Tools for Trading System

This directory contains tools for backing up the trading system to AWS S3.

## Scripts

### backup_to_s3.py

Creates a backup archive of the trading system and uploads it to an AWS S3 bucket.

**Usage:**
```bash
python tools/backup/backup_to_s3.py [--output-dir DIR] [--include-venv] [--max-backups NUM] [--no-upload] [--bucket BUCKET_NAME] [--region REGION] [--access-key ACCESS_KEY] [--secret-key SECRET_KEY] [--test]
```

**Options:**
- `--output-dir`: Directory to save the backup archive (default: project root)
- `--include-venv`: Include the virtual environment in the backup
- `--max-backups`: Maximum number of backups to keep locally (default: 5)
- `--no-upload`: Skip uploading to AWS S3
- `--bucket`: AWS S3 bucket name
- `--region`: AWS region (e.g., us-east-1)
- `--access-key`: AWS access key ID
- `--secret-key`: AWS secret access key
- `--test`: Create a smaller test backup with only essential files

### schedule_s3_backup.py

Sets up automatic backups of the trading system to AWS S3 at specified intervals.

**Usage:**
```bash
python tools/backup/schedule_s3_backup.py [--interval MINUTES] [--no-change-detection] [--daemon] [--bucket BUCKET_NAME] [--region REGION] [--access-key ACCESS_KEY] [--secret-key SECRET_KEY]
```

**Options:**
- `--interval`: Minimum time between backups in minutes (default: 60)
- `--no-change-detection`: Disable change detection (backup at fixed intervals)
- `--daemon`: Run as a background daemon process
- `--bucket`: AWS S3 bucket name
- `--region`: AWS region (e.g., us-east-1)
- `--access-key`: AWS access key ID
- `--secret-key`: AWS secret access key

### configure_aws_cli.py

Configures the AWS CLI with credentials from aws_config.py.

**Usage:**
```bash
python tools/backup/configure_aws_cli.py
```

This script:
- Creates the necessary AWS CLI configuration files in the `~/.aws` directory
- Sets up the credentials and region from your aws_config.py file
- Makes the configuration files readable only by the owner for security

### aws_config.py

Configuration file for AWS credentials and backup settings.

## Setup Instructions

### 1. Install Required Dependencies

```bash
pip install boto3 awscli
```

### 2. Set Up AWS S3 Bucket

1. Log in to the [AWS Management Console](https://aws.amazon.com/console/)
2. Go to the S3 service
3. Create a new bucket with a unique name
4. Note the bucket name and region for later use

### 3. Set Up AWS Credentials

#### Option 1: Edit aws_config.py (Recommended for VPS)

Edit the `aws_config.py` file and fill in your AWS credentials:

```python
AWS_ACCESS_KEY_ID = "your_access_key"
AWS_SECRET_ACCESS_KEY = "your_secret_key"
AWS_REGION = "your_region"  # e.g., us-east-1
S3_BUCKET_NAME = "your_bucket_name"
```

#### Option 2: Configure AWS CLI with our script

After setting up aws_config.py, run:

```bash
python tools/backup/configure_aws_cli.py
```

This will automatically create the necessary AWS CLI configuration files using your credentials from aws_config.py.

#### Option 3: Use AWS CLI Configuration Manually

If you have the AWS CLI installed, you can configure credentials with:

```bash
aws configure
```

This will create a `~/.aws/credentials` file that boto3 can use automatically.

### 4. Run a Manual Backup

```bash
# Full backup
python tools/backup/backup_to_s3.py

# Test backup (smaller size)
python tools/backup/backup_to_s3.py --test
```

### 5. Set Up Automatic Backups

```bash
# Run backups every hour when changes are detected
python tools/backup/schedule_s3_backup.py --interval 60 --daemon
```

## Backup Strategy

- Backups are created as ZIP archives with timestamps in the filename
- By default, only tracked files are included in the backup
- **Important sensitive files** like `.env`, `client_secrets.json`, and `credentials.json` are **explicitly included** in the backup even though they're excluded from Git
- The virtual environment is excluded by default to reduce backup size
- Old backups are automatically cleaned up locally to save space
- Backups are uploaded to a "trading_system_backups" folder in your S3 bucket
- Change detection ensures backups are only created when files have changed
- Test backups can be created with the `--test` flag for quick verification of the backup process

## Monitoring Backups

Check the `s3_backup_scheduler.log` file for information about automatic backups.

You can list your S3 backups with:

```bash
aws s3 ls s3://your-bucket-name/trading_system_backups/
```

## Security Considerations

- AWS credentials are sensitive information. Never commit `aws_config.py` with real credentials to Git.
- Consider using IAM roles with limited permissions for the backup user.
- Enable versioning on your S3 bucket for additional protection against accidental deletions.
- Consider enabling encryption for your S3 bucket for sensitive data. 