#!/usr/bin/env python3
"""
Simple Strategy Trading Agent

This agent implements a simple moving average crossover strategy.
It can be used as a baseline for comparing more complex strategies.
"""

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class SimpleStrategyAgent:
    """
    A trading agent that implements a simple moving average crossover strategy.
    """
    
    def __init__(self, symbol="BTC/USD", fast_period=20, slow_period=50, 
                 data_source="historical", backtest_days=365, log_dir="logs"):
        """
        Initialize the simple strategy agent
        
        Args:
            symbol: Trading pair symbol
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            data_source: Source of data ('historical' or 'live')
            backtest_days: Number of days to use for backtesting
            log_dir: Directory to save logs and results
        """
        self.symbol = symbol
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.data_source = data_source
        self.backtest_days = backtest_days
        self.log_dir = log_dir
        self.data = None
        self.signals = None
        self.positions = None
        self.portfolio = None
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        print(f"Initializing simple strategy agent:")
        print(f"  Symbol: {self.symbol}")
        print(f"  Strategy: {self.fast_period}/{self.slow_period} MA Crossover")
        print(f"  Data source: {self.data_source}")
    
    def load_data(self):
        """Load historical or live data"""
        if self.data_source == "historical":
            self._load_historical_data()
        else:
            self._load_live_data()
    
    def _load_historical_data(self):
        """Load historical data for backtesting"""
        print(f"Loading historical data for {self.symbol}...")
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.backtest_days)
        dates = pd.date_range(start=start_date, end=end_date, freq='1h')
        
        # Generate simulated price data
        n = len(dates)
        seed = np.random.randint(0, 10000)  # Random seed for reproducibility
        np.random.seed(seed)
        
        # Start with a base price and add random walk
        base_price = 30000  # Starting price for BTC/USD
        random_walk = np.random.randn(n).cumsum() * 100
        trend = np.linspace(0, 2000, n)  # Add a slight upward trend
        
        close_values = base_price + random_walk + trend
        high_values = close_values * (1 + 0.01 * np.random.rand(n))
        low_values = close_values * (1 - 0.01 * np.random.rand(n))
        open_values = close_values.copy()
        
        # Shift open values
        open_values = np.roll(open_values, 1)
        open_values[0] = close_values[0] * (1 - 0.005 + 0.01 * np.random.rand())
        
        # Generate volume with some randomness
        volume_base = np.random.randint(100, 1000, size=n)
        volume_trend = np.sin(np.linspace(0, 10, n)) * 200 + 500  # Add cyclical pattern
        volume_values = volume_base + volume_trend
        
        # Create DataFrame
        self.data = pd.DataFrame({
            'timestamp': dates,
            'open': open_values,
            'high': high_values,
            'low': low_values,
            'close': close_values,
            'volume': volume_values
        })
        
        print(f"Loaded {len(self.data)} historical data points")
        
        # Save the first and last few rows to a log file
        log_file = os.path.join(self.log_dir, f"{self.symbol.replace('/', '_')}_data.log")
        with open(log_file, 'w') as f:
            f.write("=== First 5 rows ===\n")
            f.write(str(self.data.head()) + "\n\n")
            f.write("=== Last 5 rows ===\n")
            f.write(str(self.data.tail()) + "\n")
    
    def _load_live_data(self):
        """Load live market data"""
        print(f"Loading live data for {self.symbol}...")
        # In a real implementation, this would connect to an exchange API
        # For now, we'll just use the same simulated data
        self._load_historical_data()
        print("Note: Using simulated data instead of live data")
    
    def generate_signals(self):
        """Generate trading signals based on moving average crossover"""
        print("Generating trading signals...")
        
        if self.data is None:
            self.load_data()
        
        # Calculate moving averages
        self.data['fast_ma'] = self.data['close'].rolling(window=self.fast_period).mean()
        self.data['slow_ma'] = self.data['close'].rolling(window=self.slow_period).mean()
        
        # Initialize signals DataFrame
        self.signals = pd.DataFrame(index=self.data.index)
        self.signals['signal'] = 0.0
        
        # Generate buy/sell signals
        # Buy signal (1) when fast MA crosses above slow MA
        # Sell signal (-1) when fast MA crosses below slow MA
        self.signals['signal'] = np.where(self.data['fast_ma'] > self.data['slow_ma'], 1.0, 0.0)
        
        # Generate trading orders (1 for buy, -1 for sell)
        self.signals['position'] = self.signals['signal'].diff()
        
        print(f"Generated {len(self.signals[self.signals['position'] != 0])} trading signals")
    
    def backtest_strategy(self, initial_capital=10000.0):
        """Backtest the strategy with historical data"""
        print(f"Backtesting strategy with {initial_capital} initial capital...")
        
        if self.signals is None:
            self.generate_signals()
        
        # Create a DataFrame for positions and portfolio
        self.positions = pd.DataFrame(index=self.signals.index).fillna(0.0)
        self.portfolio = pd.DataFrame(index=self.signals.index).fillna(0.0)
        
        # Store positions and asset values
        self.positions['position'] = self.signals['signal']
        self.positions['asset'] = self.positions['position'] * self.data['close']
        
        # Initialize portfolio with initial capital
        self.portfolio['positions'] = self.positions['asset']
        self.portfolio['cash'] = initial_capital - (self.signals['position'] * self.data['close']).cumsum()
        
        # Add transaction costs (0.1% per trade)
        trade_cost = 0.001
        trades = self.signals['position'].abs()
        self.portfolio['trade_costs'] = trades * self.data['close'] * trade_cost
        self.portfolio['cash'] = self.portfolio['cash'] - self.portfolio['trade_costs'].cumsum()
        
        # Calculate total portfolio value
        self.portfolio['total'] = self.portfolio['positions'] + self.portfolio['cash']
        
        # Calculate returns
        self.portfolio['returns'] = self.portfolio['total'].pct_change()
        
        # Calculate cumulative returns
        self.portfolio['cumulative_returns'] = (1 + self.portfolio['returns']).cumprod()
        
        # Calculate drawdown
        self.portfolio['peak'] = self.portfolio['total'].cummax()
        self.portfolio['drawdown'] = (self.portfolio['total'] - self.portfolio['peak']) / self.portfolio['peak']
        
        # Calculate performance metrics
        total_return = (self.portfolio['total'].iloc[-1] / initial_capital) - 1.0
        annual_return = total_return / (self.backtest_days / 365)
        sharpe_ratio = np.sqrt(252) * self.portfolio['returns'].mean() / self.portfolio['returns'].std()
        max_drawdown = self.portfolio['drawdown'].min()
        win_rate = len(self.portfolio[self.portfolio['returns'] > 0]) / len(self.portfolio[self.portfolio['returns'] != 0])
        
        print(f"Backtest Results:")
        print(f"  Total Return: {total_return:.2%}")
        print(f"  Annual Return: {annual_return:.2%}")
        print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {max_drawdown:.2%}")
        print(f"  Win Rate: {win_rate:.2%}")
        
        # Save results to log file
        log_file = os.path.join(self.log_dir, f"{self.symbol.replace('/', '_')}_backtest.log")
        with open(log_file, 'w') as f:
            f.write(f"Backtest Results for {self.symbol}\n")
            f.write(f"Strategy: {self.fast_period}/{self.slow_period} MA Crossover\n")
            f.write(f"Period: {self.backtest_days} days\n")
            f.write(f"Initial Capital: ${initial_capital}\n\n")
            f.write(f"Total Return: {total_return:.2%}\n")
            f.write(f"Annual Return: {annual_return:.2%}\n")
            f.write(f"Sharpe Ratio: {sharpe_ratio:.2f}\n")
            f.write(f"Max Drawdown: {max_drawdown:.2%}\n")
            f.write(f"Win Rate: {win_rate:.2%}\n\n")
            f.write(f"Final Portfolio Value: ${self.portfolio['total'].iloc[-1]:.2f}\n")
            f.write(f"Number of Trades: {len(self.signals[self.signals['position'] != 0])}\n")
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }
    
    def plot_results(self):
        """Plot the backtest results"""
        if self.portfolio is None:
            print("No backtest results to plot. Run backtest_strategy() first.")
            return
        
        print("Plotting backtest results...")
        
        # Create figure with subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)
        
        # Plot price and moving averages
        axes[0].plot(self.data.index, self.data['close'], label='Price')
        axes[0].plot(self.data.index, self.data['fast_ma'], label=f'{self.fast_period} MA')
        axes[0].plot(self.data.index, self.data['slow_ma'], label=f'{self.slow_period} MA')
        
        # Plot buy/sell signals
        buy_signals = self.signals[self.signals['position'] == 1.0]
        sell_signals = self.signals[self.signals['position'] == -1.0]
        
        axes[0].plot(buy_signals.index, self.data.loc[buy_signals.index, 'close'], 
                    '^', markersize=10, color='g', label='Buy')
        axes[0].plot(sell_signals.index, self.data.loc[sell_signals.index, 'close'], 
                    'v', markersize=10, color='r', label='Sell')
        
        axes[0].set_title(f'{self.symbol} Price and Moving Averages')
        axes[0].set_ylabel('Price')
        axes[0].legend()
        axes[0].grid(True)
        
        # Plot portfolio value
        axes[1].plot(self.portfolio.index, self.portfolio['total'], label='Portfolio Value')
        axes[1].set_title('Portfolio Value')
        axes[1].set_ylabel('Value ($)')
        axes[1].legend()
        axes[1].grid(True)
        
        # Plot drawdown
        axes[2].fill_between(self.portfolio.index, self.portfolio['drawdown'], 0, 
                            color='r', alpha=0.3)
        axes[2].set_title('Drawdown')
        axes[2].set_ylabel('Drawdown (%)')
        axes[2].set_xlabel('Date')
        axes[2].grid(True)
        
        # Format x-axis
        plt.tight_layout()
        
        # Save the plot
        plot_file = os.path.join(self.log_dir, f"{self.symbol.replace('/', '_')}_backtest_plot.png")
        plt.savefig(plot_file)
        print(f"Plot saved to {plot_file}")
        
        # Close the plot to free memory
        plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description='Simple Moving Average Crossover Strategy')
    parser.add_argument('--symbol', type=str, default="BTC/USD",
                        help='Trading pair symbol (default: BTC/USD)')
    parser.add_argument('--fast', type=int, default=20,
                        help='Fast moving average period (default: 20)')
    parser.add_argument('--slow', type=int, default=50,
                        help='Slow moving average period (default: 50)')
    parser.add_argument('--data', type=str, default="historical", choices=['historical', 'live'],
                        help='Data source (default: historical)')
    parser.add_argument('--days', type=int, default=365,
                        help='Number of days for backtesting (default: 365)')
    parser.add_argument('--capital', type=float, default=10000.0,
                        help='Initial capital for backtesting (default: 10000.0)')
    parser.add_argument('--log-dir', type=str, default="logs",
                        help='Directory to save logs and results (default: logs)')
    
    args = parser.parse_args()
    
    agent = SimpleStrategyAgent(
        symbol=args.symbol,
        fast_period=args.fast,
        slow_period=args.slow,
        data_source=args.data,
        backtest_days=args.days,
        log_dir=args.log_dir
    )
    
    agent.load_data()
    agent.generate_signals()
    agent.backtest_strategy(initial_capital=args.capital)
    agent.plot_results()

if __name__ == "__main__":
    main() 