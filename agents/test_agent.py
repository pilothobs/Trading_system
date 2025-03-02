#!/usr/bin/env python3
"""
Test Agent

This script simulates a trading agent with configurable CPU and memory usage.
It's used to test resource monitoring and determine if a cloud GPU is needed.
"""

import os
import sys
import time
import random
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class TestAgent:
    """
    A test agent that simulates CPU and memory usage similar to a trading agent.
    """
    
    def __init__(self, cpu_intensity=50, memory_mb=500, duration=300):
        """
        Initialize the test agent
        
        Args:
            cpu_intensity: CPU usage intensity (0-100)
            memory_mb: Memory to allocate in MB
            duration: Duration to run in seconds
        """
        self.cpu_intensity = min(max(cpu_intensity, 0), 100)
        self.memory_mb = memory_mb
        self.duration = duration
        self.data = None
        self.models = []
        
        print(f"Initializing test agent with:")
        print(f"  CPU intensity: {self.cpu_intensity}%")
        print(f"  Memory allocation: {self.memory_mb} MB")
        print(f"  Duration: {self.duration} seconds")
    
    def generate_test_data(self):
        """Generate test market data"""
        print("Generating test market data...")
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        dates = pd.date_range(start=start_date, end=end_date, freq='1h')
        
        # Generate price data
        n = len(dates)
        close_values = 100 * (1 + 0.1 * np.random.randn(n).cumsum() / np.sqrt(n))
        high_values = close_values * (1 + 0.02 * np.random.rand(n))
        low_values = close_values * (1 - 0.02 * np.random.rand(n))
        volume_values = np.random.randint(1000, 10000, size=n)
        
        # Create DataFrame first
        self.data = pd.DataFrame({
            'timestamp': dates,
            'close': close_values,
            'high': high_values,
            'low': low_values,
            'volume': volume_values
        })
        
        # Now we can use pandas shift on the DataFrame
        self.data['open'] = self.data['close'].shift(1).fillna(method='bfill')
        
        # Allocate memory based on memory_mb
        target_bytes = self.memory_mb * 1024 * 1024
        current_bytes = sys.getsizeof(self.data)
        
        # Create additional dataframes to reach target memory
        if current_bytes < target_bytes:
            remaining_bytes = target_bytes - current_bytes
            copies_needed = int(remaining_bytes / current_bytes) + 1
            
            print(f"Allocating {self.memory_mb} MB of memory...")
            for i in range(copies_needed):
                # Create a copy with slight modifications to prevent optimization
                copy_data = self.data.copy()
                copy_data['close'] = copy_data['close'] * (1 + 0.001 * random.random())
                self.models.append(copy_data)
        
        print(f"Generated data with {len(self.data)} rows")
    
    def run_cpu_intensive_task(self, seconds):
        """
        Run a CPU-intensive task for the specified number of seconds
        
        Args:
            seconds: Number of seconds to run the task
        """
        print(f"Running CPU-intensive task for {seconds} seconds...")
        
        # Calculate how many iterations to run based on CPU intensity
        # Higher intensity = more iterations per second
        iterations_per_second = 10000 * (self.cpu_intensity / 100)
        total_iterations = int(iterations_per_second * seconds)
        
        start_time = time.time()
        
        # Perform CPU-intensive calculations
        for i in range(total_iterations):
            # Matrix operations are CPU-intensive
            size = 50  # Matrix size
            a = np.random.rand(size, size)
            b = np.random.rand(size, size)
            c = np.dot(a, b)  # Matrix multiplication
            
            # Add some randomness to prevent compiler optimizations
            if random.random() < 0.0001:
                print(f"Matrix sum: {c.sum():.2f}")
            
            # Check if we've exceeded the requested time
            if i % 1000 == 0 and time.time() - start_time >= seconds:
                break
        
        elapsed = time.time() - start_time
        print(f"CPU task completed in {elapsed:.2f} seconds")
    
    def simulate_trading(self):
        """Simulate trading activity"""
        print("Starting trading simulation...")
        
        if self.data is None:
            self.generate_test_data()
        
        start_time = time.time()
        end_time = start_time + self.duration
        
        iteration = 0
        while time.time() < end_time:
            iteration += 1
            print(f"Trading iteration {iteration}...")
            
            # Simulate data processing (low CPU)
            self.data['sma_20'] = self.data['close'].rolling(window=20).mean()
            self.data['sma_50'] = self.data['close'].rolling(window=50).mean()
            self.data['rsi'] = self._calculate_rsi(self.data['close'], 14)
            
            # Simulate signal generation (medium CPU)
            signals = self._generate_signals()
            
            # Simulate model training/prediction (high CPU)
            cpu_time = 2 + (self.cpu_intensity / 100) * 8  # 2-10 seconds based on intensity
            self.run_cpu_intensive_task(cpu_time)
            
            # Simulate trade execution (low CPU)
            self._execute_trades(signals)
            
            # Sleep to simulate waiting for next candle
            time.sleep(1)
        
        total_time = time.time() - start_time
        print(f"Trading simulation completed after {total_time:.2f} seconds")
    
    def _calculate_rsi(self, prices, window=14):
        """Calculate RSI indicator"""
        # Convert to numpy array for calculations
        price_array = prices.values
        deltas = np.diff(price_array)
        
        # Handle empty arrays
        if len(deltas) < window+1:
            return np.zeros_like(price_array)
            
        seed = deltas[:window+1]
        up = seed[seed >= 0].sum()/window if any(seed >= 0) else 0
        down = -seed[seed < 0].sum()/window if any(seed < 0) else 0.0001  # Avoid division by zero
        
        rs = up/down
        rsi = np.zeros_like(price_array)
        rsi[:window] = 100. - 100./(1. + rs)
        
        for i in range(window, len(price_array)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (window - 1) + upval) / window
            down = (down * (window - 1) + downval) / window
            
            # Avoid division by zero
            if down == 0:
                down = 0.0001
                
            rs = up/down
            rsi[i] = 100. - 100./(1. + rs)
        
        return pd.Series(rsi, index=prices.index)
    
    def _generate_signals(self):
        """Generate trading signals"""
        signals = pd.DataFrame(index=self.data.index)
        signals['signal'] = 0
        
        # Simple moving average crossover strategy
        signals.loc[self.data['sma_20'] > self.data['sma_50'], 'signal'] = 1
        signals.loc[self.data['sma_20'] < self.data['sma_50'], 'signal'] = -1
        
        # Add RSI filter
        signals.loc[self.data['rsi'] > 70, 'signal'] = -1
        signals.loc[self.data['rsi'] < 30, 'signal'] = 1
        
        return signals
    
    def _execute_trades(self, signals):
        """Simulate trade execution"""
        # Just a placeholder for a real trading execution
        positions = signals['signal'].diff()
        trades = positions[positions != 0]
        if len(trades) > 0:
            print(f"Executed {len(trades)} trades")

def main():
    parser = argparse.ArgumentParser(description='Test agent with configurable resource usage')
    parser.add_argument('--cpu', type=int, default=50,
                        help='CPU usage intensity (0-100, default: 50)')
    parser.add_argument('--memory', type=int, default=500,
                        help='Memory to allocate in MB (default: 500)')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration to run in seconds (default: 300)')
    
    args = parser.parse_args()
    
    agent = TestAgent(
        cpu_intensity=args.cpu,
        memory_mb=args.memory,
        duration=args.duration
    )
    
    agent.simulate_trading()

if __name__ == "__main__":
    main() 