#!/usr/bin/env python3
"""
Test Resource Usage

This script runs a trading agent and monitors its resource usage.
It helps determine if a cloud GPU is needed for your trading system.
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path

def run_agent_with_monitoring(agent_script, duration=300, interval=5):
    """
    Run an agent script while monitoring its resource usage
    
    Args:
        agent_script: Path to the agent script to run
        duration: Duration to run the test in seconds
        interval: Interval between resource measurements in seconds
    """
    # Get the absolute path to the agent script
    agent_path = Path(agent_script).resolve()
    if not agent_path.exists():
        print(f"Error: Agent script {agent_path} does not exist")
        return
    
    # Get the directory of this script
    current_dir = Path(__file__).parent
    
    # Start the agent in a separate process
    print(f"Starting agent: {agent_path}")
    agent_process = subprocess.Popen(
        [sys.executable, str(agent_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the agent a moment to start
    time.sleep(2)
    
    if agent_process.poll() is not None:
        # Agent failed to start
        stdout, stderr = agent_process.communicate()
        print(f"Error: Agent failed to start")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return
    
    # Start the resource monitor
    print(f"Starting resource monitor for {duration} seconds")
    monitor_path = current_dir / "resource_monitor.py"
    monitor_process = subprocess.Popen(
        [
            sys.executable, 
            str(monitor_path),
            "--python-only",
            "--interval", str(interval),
            "--duration", str(duration)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for the monitoring to complete
        monitor_stdout, monitor_stderr = monitor_process.communicate()
        
        # Print monitoring output
        print("\nResource Monitoring Results:")
        print(monitor_stdout)
        
        if monitor_stderr:
            print("Monitoring Errors:")
            print(monitor_stderr)
        
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        # Clean up processes
        if agent_process.poll() is None:
            print("Terminating agent process...")
            agent_process.terminate()
            try:
                agent_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                agent_process.kill()
        
        if monitor_process.poll() is None:
            print("Terminating monitor process...")
            monitor_process.terminate()
            try:
                monitor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                monitor_process.kill()
    
    # Get agent output
    agent_stdout, agent_stderr = agent_process.communicate()
    
    print("\nAgent Output:")
    print(agent_stdout)
    
    if agent_stderr:
        print("Agent Errors:")
        print(agent_stderr)
    
    print("\nTest complete. Check the logs directory for detailed resource usage data.")

def main():
    parser = argparse.ArgumentParser(description='Test resource usage of a trading agent')
    parser.add_argument('agent_script', help='Path to the agent script to run')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration to run the test in seconds (default: 300)')
    parser.add_argument('--interval', type=int, default=5,
                        help='Interval between resource measurements in seconds (default: 5)')
    
    args = parser.parse_args()
    
    run_agent_with_monitoring(args.agent_script, args.duration, args.interval)

if __name__ == "__main__":
    main() 