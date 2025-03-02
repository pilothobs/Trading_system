#!/usr/bin/env python3
"""
Trading System Backup Script

This script backs up the entire trading system to Google Drive.
It can be run manually or scheduled to run periodically.
"""

import os
import sys
import time
import datetime
import shutil
import subprocess
import argparse
from pathlib import Path

# Add Google Drive API libraries
try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    print("Warning: pydrive2 not installed. Google Drive backup disabled.")
    print("Install with: pip install pydrive2")

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
    
    print(f"Creating backup archive: {backup_path}")
    
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
                print(f"Including sensitive file in backup: {file}")
                backup_files.add(file)
        
        # Create the zip archive
        shutil.make_archive(
            str(backup_path.with_suffix("")),  # Remove .zip extension
            "zip",
            root_dir=project_root,
            base_dir="."
        )
        
        print(f"Backup archive created: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"Error creating backup archive: {e}")
        return None

def upload_to_google_drive(file_path, folder_name="Trading System Backups"):
    """
    Upload a file to Google Drive
    
    Args:
        file_path: Path to the file to upload
        folder_name: Name of the folder in Google Drive to upload to
        
    Returns:
        True if successful, False otherwise
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        print("Google Drive API not available. Skipping upload.")
        return False
    
    try:
        print(f"Authenticating with Google Drive...")
        # Get the directory where this script is located
        script_dir = Path(__file__).parent.absolute()
        
        # Set up the GoogleAuth object with the correct paths
        gauth = GoogleAuth()
        
        # Set the client secrets file path
        client_secrets_path = script_dir / "client_secrets.json"
        gauth.settings['client_config_file'] = str(client_secrets_path)
        
        # Set the credentials file path
        credentials_path = script_dir / "credentials.json"
        
        # Try to load saved client credentials
        gauth.LoadCredentialsFile(str(credentials_path))
        
        if gauth.credentials is None:
            # Use the CommandLineAuth method which works better in headless environments
            print("No stored credentials found. Starting new authentication flow.")
            print("Please follow the instructions below to authenticate:")
            gauth.CommandLineAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            print("Refreshing expired credentials...")
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
            
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(str(credentials_path))
        
        drive = GoogleDrive(gauth)
        
        # Find or create the backup folder
        folder_id = None
        file_list = drive.ListFile({'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
        
        if file_list:
            folder_id = file_list[0]['id']
            print(f"Found backup folder: {folder_name}")
        else:
            # Create the folder if it doesn't exist
            folder = drive.CreateFile({
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            })
            folder.Upload()
            folder_id = folder['id']
            print(f"Created backup folder: {folder_name}")
        
        # Upload the file
        file_name = os.path.basename(file_path)
        drive_file = drive.CreateFile({
            'title': file_name,
            'parents': [{'id': folder_id}]
        })
        drive_file.SetContentFile(str(file_path))
        
        print(f"Uploading {file_name} to Google Drive...")
        drive_file.Upload()
        
        print(f"Successfully uploaded to Google Drive: {file_name}")
        return True
        
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
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
            print(f"Removing old backup: {backup}")
            backup.unlink()

def main():
    parser = argparse.ArgumentParser(description='Backup trading system to Google Drive')
    parser.add_argument('--output-dir', help='Directory to save the backup archive')
    parser.add_argument('--include-venv', action='store_true', help='Include virtual environment in backup')
    parser.add_argument('--max-backups', type=int, default=5, help='Maximum number of backups to keep')
    parser.add_argument('--no-upload', action='store_true', help='Skip uploading to Google Drive')
    
    args = parser.parse_args()
    
    # Create the backup archive
    backup_path = create_backup_archive(args.output_dir, args.include_venv)
    
    if backup_path:
        # Upload to Google Drive
        if not args.no_upload and GOOGLE_DRIVE_AVAILABLE:
            print("\nNOTE: Google Drive upload requires additional setup.")
            print("For now, your backup has been created locally at:")
            print(f"  {backup_path}")
            print("\nTo set up Google Drive integration:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a project and enable the Google Drive API")
            print("3. Create OAuth credentials (Desktop app)")
            print("4. Download the credentials JSON file")
            print("5. Save it as 'client_secrets.json' in the tools/backup directory")
            print("\nAlternatively, you can manually upload the backup to Google Drive through the web interface.")
        else:
            print(f"\nBackup created successfully at: {backup_path}")
            
        # Cleanup old backups
        cleanup_old_backups(backup_path.parent, args.max_backups)
    
if __name__ == "__main__":
    main() 