#!/usr/bin/env python3
"""
Resource Monitor for Trading System Agents

This script monitors CPU and RAM usage of specified processes or all Python processes.
It logs the data and provides real-time feedback to help determine if a GPU is needed.
"""

import os
import sys
import time
import datetime
import psutil
import argparse
import logging
from pathlib import Path

# Set up logging
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"resource_usage_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_process_info(process):
    """Get CPU and memory usage for a process"""
    try:
        with process.oneshot():
            # Get CPU usage as a percentage
            cpu_percent = process.cpu_percent(interval=None)
            
            # Get memory usage in MB
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get process name and command line
            name = process.name()
            try:
                cmdline = ' '.join(process.cmdline())
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cmdline = "Access Denied"
                
            return {
                'pid': process.pid,
                'name': name,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'cmdline': cmdline
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def monitor_processes(process_filter=None, interval=5, duration=None):
    """
    Monitor system processes and log their resource usage
    
    Args:
        process_filter: Function to filter processes (e.g., lambda p: 'python' in p.name())
        interval: Seconds between measurements
        duration: Total monitoring duration in seconds (None for indefinite)
    """
    system_info = {
        'cpu_count': psutil.cpu_count(logical=True),
        'cpu_count_physical': psutil.cpu_count(logical=False),
        'total_memory_gb': psutil.virtual_memory().total / (1024**3)
    }
    
    logging.info(f"System: {system_info['cpu_count']} logical CPUs, "
                f"{system_info['cpu_count_physical']} physical CPUs, "
                f"{system_info['total_memory_gb']:.2f} GB RAM")
    
    start_time = time.time()
    iteration = 0
    
    try:
        while True:
            iteration += 1
            current_time = time.time()
            elapsed = current_time - start_time
            
            if duration and elapsed > duration:
                break
                
            # Get all processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if process_filter is None or process_filter(proc):
                    info = get_process_info(proc)
                    if info:
                        processes.append(info)
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Log system-wide stats
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            logging.info(f"Iteration {iteration} - System CPU: {cpu_percent:.1f}%, "
                        f"Memory: {memory_percent:.1f}%")
            
            # Log top processes
            for i, proc in enumerate(processes[:10]):  # Top 10 processes
                logging.info(f"  {i+1}. PID {proc['pid']} ({proc['name']}): "
                           f"CPU {proc['cpu_percent']:.1f}%, "
                           f"Memory {proc['memory_mb']:.1f} MB")
            
            # Calculate totals for filtered processes
            if processes:
                total_cpu = sum(p['cpu_percent'] for p in processes)
                total_memory_mb = sum(p['memory_mb'] for p in processes)
                logging.info(f"Total for monitored processes: CPU {total_cpu:.1f}%, "
                           f"Memory {total_memory_mb:.1f} MB")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
    
    logging.info(f"Monitoring complete. Duration: {time.time() - start_time:.1f} seconds")

def main():
    parser = argparse.ArgumentParser(description='Monitor CPU and RAM usage of processes')
    parser.add_argument('--python-only', action='store_true', 
                        help='Monitor only Python processes')
    parser.add_argument('--agent-only', action='store_true',
                        help='Monitor only trading agent processes')
    parser.add_argument('--interval', type=int, default=5,
                        help='Seconds between measurements (default: 5)')
    parser.add_argument('--duration', type=int, default=None,
                        help='Total monitoring duration in seconds (default: indefinite)')
    
    args = parser.parse_args()
    
    # Define process filter based on arguments
    process_filter = None
    if args.python_only:
        process_filter = lambda p: 'python' in p.name().lower()
    elif args.agent_only:
        # This assumes your agents have a specific pattern in their command line
        # Adjust as needed based on how you launch your agents
        process_filter = lambda p: ('python' in p.name().lower() and 
                                  any(agent in ' '.join(p.cmdline()).lower() 
                                      for agent in ['agent', 'strategy', 'backtesting']))
    
    logging.info(f"Starting resource monitoring with {args.interval}s interval")
    if process_filter:
        if args.python_only:
            logging.info("Monitoring Python processes only")
        elif args.agent_only:
            logging.info("Monitoring trading agent processes only")
    else:
        logging.info("Monitoring all processes")
    
    monitor_processes(process_filter, args.interval, args.duration)

if __name__ == "__main__":
    main() 