#!/usr/bin/env python3
"""
Schedule Automatic Backups

This script sets up automatic backups of the trading system at specified intervals.
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
        logging.FileHandler("backup_scheduler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

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
    
    return hasher.hexdigest()

def run_backup():
    """Run the backup script"""
    backup_script = Path(__file__).parent / "backup_to_drive.py"
    
    try:
        logging.info("Running backup...")
        result = subprocess.run(
            [sys.executable, str(backup_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Backup completed successfully")
            for line in result.stdout.splitlines():
                logging.info(f"  {line}")
        else:
            logging.error("Backup failed")
            logging.error(f"Error: {result.stderr}")
            
        return result.returncode == 0
    
    except Exception as e:
        logging.error(f"Failed to run backup: {e}")
        return False

def monitor_changes(interval_minutes=60, change_detection=True):
    """
    Monitor the project for changes and run backups
    
    Args:
        interval_minutes: Minimum time between backups in minutes
        change_detection: Whether to only backup when changes are detected
    """
    logging.info(f"Starting backup scheduler")
    logging.info(f"  Interval: {interval_minutes} minutes")
    logging.info(f"  Change detection: {'enabled' if change_detection else 'disabled'}")
    
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
                    success = run_backup()
                    if success:
                        last_backup_time = time.time()
            
            # Sleep for a while before checking again
            # Use a shorter sleep time to be more responsive to changes
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logging.info("Backup scheduler stopped by user")

def main():
    parser = argparse.ArgumentParser(description='Schedule automatic backups of the trading system')
    parser.add_argument('--interval', type=int, default=60,
                        help='Minimum time between backups in minutes (default: 60)')
    parser.add_argument('--no-change-detection', action='store_true',
                        help='Disable change detection (backup at fixed intervals)')
    parser.add_argument('--daemon', action='store_true',
                        help='Run as a background daemon process')
    
    args = parser.parse_args()
    
    if args.daemon:
        # Fork the process to run in the background
        try:
            pid = os.fork()
            if pid > 0:
                # Exit the parent process
                logging.info(f"Backup scheduler started in background (PID: {pid})")
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
    monitor_changes(args.interval, not args.no_change_detection)

if __name__ == "__main__":
    main() 