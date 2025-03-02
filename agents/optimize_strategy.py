#!/usr/bin/env python3
"""
Strategy Optimizer

This script optimizes the parameters of the simple moving average crossover strategy
by testing different combinations of fast and slow moving average periods.
"""

import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from itertools import product
from simple_strategy_agent import SimpleStrategyAgent

def optimize_strategy(symbol="BTC/USD", days=180, capital=10000.0, 
                     fast_range=(5, 50, 5), slow_range=(10, 100, 10),
                     metric="sharpe_ratio", log_dir="logs"):
    """
    Optimize strategy parameters by testing different combinations
    
    Args:
        symbol: Trading pair symbol
        days: Number of days for backtesting
        capital: Initial capital for backtesting
        fast_range: Range for fast MA (start, end, step)
        slow_range: Range for slow MA (start, end, step)
        metric: Metric to optimize ('sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate')
        log_dir: Directory to save logs and results
    
    Returns:
        Tuple of (best_fast, best_slow, best_result, results_df)
    """
    print(f"Optimizing strategy for {symbol} over {days} days...")
    print(f"Fast MA range: {fast_range[0]}-{fast_range[1]} (step {fast_range[2]})")
    print(f"Slow MA range: {slow_range[0]}-{slow_range[1]} (step {slow_range[2]})")
    print(f"Optimizing for: {metric}")
    
    # Create ranges for fast and slow periods
    fast_periods = range(fast_range[0], fast_range[1] + 1, fast_range[2])
    slow_periods = range(slow_range[0], slow_range[1] + 1, slow_range[2])
    
    # Store results
    results = []
    
    # Track best result
    best_result = -np.inf if metric != "max_drawdown" else 0
    best_fast = None
    best_slow = None
    
    # Test all combinations
    total_combinations = len(fast_periods) * len(slow_periods)
    current = 0
    
    start_time = time.time()
    
    for fast, slow in product(fast_periods, slow_periods):
        # Skip invalid combinations (fast must be less than slow)
        if fast >= slow:
            continue
        
        current += 1
        print(f"Testing combination {current}/{total_combinations}: Fast MA={fast}, Slow MA={slow}")
        
        # Create agent with current parameters
        agent = SimpleStrategyAgent(
            symbol=symbol,
            fast_period=fast,
            slow_period=slow,
            data_source="historical",
            backtest_days=days,
            log_dir=log_dir
        )
        
        # Run backtest silently (redirect stdout)
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        
        try:
            agent.load_data()
            agent.generate_signals()
            backtest_results = agent.backtest_strategy(initial_capital=capital)
            
            # Restore stdout
            sys.stdout.close()
            sys.stdout = original_stdout
            
            # Get result for the metric we're optimizing
            result = backtest_results[metric]
            
            # For max_drawdown, we want to minimize the absolute value
            if metric == "max_drawdown":
                result = -result  # Convert to positive for maximization
            
            # Store result
            results.append({
                'fast_period': fast,
                'slow_period': slow,
                'total_return': backtest_results['total_return'],
                'annual_return': backtest_results['annual_return'],
                'sharpe_ratio': backtest_results['sharpe_ratio'],
                'max_drawdown': backtest_results['max_drawdown'],
                'win_rate': backtest_results['win_rate']
            })
            
            # Check if this is the best result
            if result > best_result:
                best_result = result
                best_fast = fast
                best_slow = slow
                print(f"New best result: Fast MA={fast}, Slow MA={slow}, {metric}={backtest_results[metric]:.4f}")
        
        except Exception as e:
            # Restore stdout in case of error
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"Error testing Fast MA={fast}, Slow MA={slow}: {str(e)}")
    
    elapsed_time = time.time() - start_time
    print(f"Optimization completed in {elapsed_time:.2f} seconds")
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results to CSV
    csv_file = os.path.join(log_dir, f"{symbol.replace('/', '_')}_optimization.csv")
    results_df.to_csv(csv_file, index=False)
    print(f"Results saved to {csv_file}")
    
    # Create heatmap of results
    create_heatmap(results_df, metric, symbol, log_dir)
    
    # Run backtest with best parameters and generate plot
    print(f"Running backtest with best parameters: Fast MA={best_fast}, Slow MA={best_slow}")
    best_agent = SimpleStrategyAgent(
        symbol=symbol,
        fast_period=best_fast,
        slow_period=best_slow,
        data_source="historical",
        backtest_days=days,
        log_dir=log_dir
    )
    
    best_agent.load_data()
    best_agent.generate_signals()
    best_agent.backtest_strategy(initial_capital=capital)
    best_agent.plot_results()
    
    return best_fast, best_slow, best_result, results_df

def create_heatmap(results_df, metric, symbol, log_dir):
    """Create a heatmap of optimization results"""
    print("Creating heatmap of results...")
    
    # Pivot data for heatmap
    pivot_data = results_df.pivot_table(
        index='slow_period', 
        columns='fast_period',
        values=metric
    )
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create heatmap
    if metric == "max_drawdown":
        # For drawdown, use a different colormap and invert values (more negative is worse)
        heatmap = plt.pcolormesh(
            pivot_data.columns, 
            pivot_data.index, 
            pivot_data.values, 
            cmap='RdYlGn_r'
        )
    else:
        heatmap = plt.pcolormesh(
            pivot_data.columns, 
            pivot_data.index, 
            pivot_data.values, 
            cmap='RdYlGn'
        )
    
    # Add colorbar
    plt.colorbar(heatmap, label=metric.replace('_', ' ').title())
    
    # Add labels and title
    plt.xlabel('Fast MA Period')
    plt.ylabel('Slow MA Period')
    plt.title(f'{symbol} Strategy Optimization - {metric.replace("_", " ").title()}')
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save the plot
    plot_file = os.path.join(log_dir, f"{symbol.replace('/', '_')}_{metric}_heatmap.png")
    plt.savefig(plot_file)
    print(f"Heatmap saved to {plot_file}")
    
    # Close the plot to free memory
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Optimize Moving Average Crossover Strategy')
    parser.add_argument('--symbol', type=str, default="BTC/USD",
                        help='Trading pair symbol (default: BTC/USD)')
    parser.add_argument('--days', type=int, default=180,
                        help='Number of days for backtesting (default: 180)')
    parser.add_argument('--capital', type=float, default=10000.0,
                        help='Initial capital for backtesting (default: 10000.0)')
    parser.add_argument('--fast-min', type=int, default=5,
                        help='Minimum fast MA period (default: 5)')
    parser.add_argument('--fast-max', type=int, default=50,
                        help='Maximum fast MA period (default: 50)')
    parser.add_argument('--fast-step', type=int, default=5,
                        help='Step size for fast MA period (default: 5)')
    parser.add_argument('--slow-min', type=int, default=10,
                        help='Minimum slow MA period (default: 10)')
    parser.add_argument('--slow-max', type=int, default=100,
                        help='Maximum slow MA period (default: 100)')
    parser.add_argument('--slow-step', type=int, default=10,
                        help='Step size for slow MA period (default: 10)')
    parser.add_argument('--metric', type=str, default="sharpe_ratio",
                        choices=['sharpe_ratio', 'total_return', 'annual_return', 'max_drawdown', 'win_rate'],
                        help='Metric to optimize (default: sharpe_ratio)')
    parser.add_argument('--log-dir', type=str, default="logs",
                        help='Directory to save logs and results (default: logs)')
    
    args = parser.parse_args()
    
    # Run optimization
    best_fast, best_slow, best_result, results_df = optimize_strategy(
        symbol=args.symbol,
        days=args.days,
        capital=args.capital,
        fast_range=(args.fast_min, args.fast_max, args.fast_step),
        slow_range=(args.slow_min, args.slow_max, args.slow_step),
        metric=args.metric,
        log_dir=args.log_dir
    )
    
    # Print best result
    print("\nOptimization Results:")
    print(f"Best parameters: Fast MA={best_fast}, Slow MA={best_slow}")
    
    # Get the row with the best result
    best_row = results_df[(results_df['fast_period'] == best_fast) & 
                          (results_df['slow_period'] == best_slow)].iloc[0]
    
    print(f"Performance metrics:")
    print(f"  Total Return: {best_row['total_return']:.2%}")
    print(f"  Annual Return: {best_row['annual_return']:.2%}")
    print(f"  Sharpe Ratio: {best_row['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {best_row['max_drawdown']:.2%}")
    print(f"  Win Rate: {best_row['win_rate']:.2%}")

if __name__ == "__main__":
    main() 