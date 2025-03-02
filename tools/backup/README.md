# Trading System Backup Tools

This directory contains tools for backing up the trading system to Google Drive and other locations.

## Scripts

### backup_to_drive.py

Creates a backup archive of the trading system and uploads it to Google Drive.

**Usage:**
```bash
python tools/backup/backup_to_drive.py [--output-dir DIR] [--include-venv] [--max-backups NUM] [--no-upload]
```

**Options:**
- `--output-dir`: Directory to save the backup archive (default: project root)
- `--include-venv`: Include the virtual environment in the backup
- `--max-backups`: Maximum number of backups to keep (default: 5)
- `--no-upload`: Skip uploading to Google Drive

### schedule_backup.py

Sets up automatic backups of the trading system at specified intervals.

**Usage:**
```bash
python tools/backup/schedule_backup.py [--interval MINUTES] [--no-change-detection] [--daemon]
```

**Options:**
- `--interval`: Minimum time between backups in minutes (default: 60)
- `--no-change-detection`: Disable change detection (backup at fixed intervals)
- `--daemon`: Run as a background daemon process

## Setup Instructions

### 1. Install Required Dependencies

```bash
pip install pydrive2
```

### 2. Set Up Google Drive API Access

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Drive API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Rename it to `client_secrets.json` and place it in the same directory as the backup scripts

### 3. Run a Manual Backup

```bash
python tools/backup/backup_to_drive.py
```

The first time you run this, it will open a browser window for authentication with Google.

### 4. Set Up Automatic Backups

```bash
# Run backups every hour when changes are detected
python tools/backup/schedule_backup.py --interval 60 --daemon
```

## Backup Strategy

- Backups are created as ZIP archives with timestamps in the filename
- By default, only tracked files are included in the backup
- **Important sensitive files** like `.env`, `client_secrets.json`, and `credentials.json` are **explicitly included** in the backup even though they're excluded from Git
- The virtual environment is excluded by default to reduce backup size
- Old backups are automatically cleaned up to save space
- Backups are uploaded to a "Trading System Backups" folder in Google Drive

## Monitoring Backups

Check the `backup_scheduler.log` file for information about automatic backups. 