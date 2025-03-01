import os
# Disable GPU usage
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import pandas as pd
import numpy as np
from typing import Dict, List
from fastapi import FastAPI
import requests
from datetime import datetime, timedelta
from ml_strategy_agent import MLStrategyAgent
import traceback

class TradingBacktest:
    def __init__(self, start_date: str, end_date: str, timeframe: str = "H1"):
        self.start_date = start_date
        self.end_date = end_date
        self.timeframe = timeframe
        self.trades: List[Dict] = []
        self.results = {
            'crew_pnl': [],
            'langgraph_pnl': [],
            'combined_pnl': []
        }
        self.ml_agent = MLStrategyAgent()
        self.initial_capital = 100000  # $100k starting capital

    def fetch_historical_data(self, symbol: str) -> pd.DataFrame:
        """Fetch historical data from OANDA via FastAPI"""
        try:
            url = f"http://localhost:8000/historical/{symbol}"
            params = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'timeframe': self.timeframe
            }
            
            print(f"Fetching {symbol} data from {self.start_date} to {self.end_date}")
            print(f"Timeframe: {self.timeframe}")
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            
            if not data:
                print("No historical data found for the specified period")
                return pd.DataFrame()
            
            # Convert to DataFrame and set timestamp as index
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)  # Set timestamp as index
            
            print(f"\nReceived {len(df)} candles")
            print("\nSample data:")
            print(df.head())
            
            return df
            
        except Exception as e:
            print(f"Error in fetch_historical_data: {str(e)}")
            traceback.print_exc()
            return pd.DataFrame()

    def run_crew_analysis(self, data: pd.DataFrame):
        # Import your crew_agents.py logic here
        pass

    def run_langgraph_analysis(self, data: pd.DataFrame):
        # Import your prim_gpt.py logic here
        pass

    def calculate_metrics(self, trades_df: pd.DataFrame) -> Dict:
        """Calculate comprehensive trading metrics"""
        metrics = {}
        
        # Basic Metrics
        metrics['total_trades'] = len(trades_df)
        metrics['winning_trades'] = len(trades_df[trades_df['pnl'] > 0])
        metrics['losing_trades'] = len(trades_df[trades_df['pnl'] < 0])
        
        # Profitability Metrics
        metrics['total_pnl'] = trades_df['pnl'].sum()
        metrics['win_rate'] = metrics['winning_trades'] / metrics['total_trades'] if metrics['total_trades'] > 0 else 0
        metrics['avg_win'] = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if metrics['winning_trades'] > 0 else 0
        metrics['avg_loss'] = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if metrics['losing_trades'] > 0 else 0
        metrics['profit_factor'] = abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if metrics['losing_trades'] > 0 else float('inf')
        
        # Risk Metrics
        equity_curve = self.initial_capital + trades_df['pnl'].cumsum()
        drawdowns = self.calculate_drawdowns(equity_curve)
        metrics['max_drawdown'] = drawdowns['drawdown'].max()
        metrics['max_drawdown_duration'] = drawdowns['drawdown_duration'].max()
        
        # Monthly Analysis
        monthly_pnl = trades_df.set_index('timestamp').resample('M')['pnl'].sum()
        metrics['monthly_profit_mean'] = monthly_pnl.mean()
        metrics['monthly_profit_std'] = monthly_pnl.std()
        metrics['profitable_months'] = len(monthly_pnl[monthly_pnl > 0])
        metrics['total_months'] = len(monthly_pnl)
        
        # Risk-Adjusted Returns
        metrics['sharpe_ratio'] = self.calculate_sharpe_ratio(trades_df['pnl'])
        metrics['sortino_ratio'] = self.calculate_sortino_ratio(trades_df['pnl'])
        
        return metrics
    
    def calculate_drawdowns(self, equity_curve: pd.Series) -> pd.DataFrame:
        """Calculate drawdown metrics"""
        rolling_max = equity_curve.expanding().max()
        drawdowns = pd.DataFrame({
            'equity': equity_curve,
            'previous_peaks': rolling_max,
            'drawdown': (equity_curve - rolling_max) / rolling_max * 100,
        })
        drawdowns['drawdown_duration'] = (drawdowns['drawdown'] < 0).astype(int).groupby(
            (drawdowns['drawdown'] == 0).cumsum()
        ).cumsum()
        
        return drawdowns
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sharpe ratio"""
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        if excess_returns.std() == 0:
            return 0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return 0
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    def print_performance_report(self, metrics: Dict):
        """Print detailed performance report"""
        print("\n=== PERFORMANCE REPORT ===")
        print(f"\nProfitability Metrics:")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.2%}")
        print(f"Total P&L: ${metrics['total_pnl']:,.2f}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\nRisk Metrics:")
        print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"Max Drawdown Duration: {metrics['max_drawdown_duration']} days")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        
        print(f"\nMonthly Analysis:")
        print(f"Average Monthly Profit: ${metrics['monthly_profit_mean']:,.2f}")
        print(f"Monthly Profit Std Dev: ${metrics['monthly_profit_std']:,.2f}")
        print(f"Profitable Months: {metrics['profitable_months']}/{metrics['total_months']}")

    def find_best_indicators(self, data: pd.DataFrame) -> Dict:
        """Find the best performing indicators"""
        try:
            # Calculate all indicators
            data = self.ml_agent.calculate_indicators(data)
            
            # Prepare features for analysis
            X, y, feature_names = self.ml_agent.prepare_features(data)
            
            # Get best features from ML agent
            best_features = self.ml_agent.find_best_features(X, y, feature_names)
            
            # Calculate success rate for each indicator
            indicator_performance = {}
            for feature in best_features:
                if feature in data.columns:
                    # Simple correlation with future returns
                    correlation = data[feature].corr(data['returns'].shift(-1))
                    indicator_performance[feature] = abs(correlation)
            
            return indicator_performance
            
        except Exception as e:
            print(f"Error in find_best_indicators: {e}")
            traceback.print_exc()
            return {}

    def optimize_strategy(self, data: pd.DataFrame):
        """Use ML to optimize trading strategy"""
        try:
            print("\nAnalyzing market conditions...")
            analysis = self.ml_agent.analyze_market(data)
            
            print(f"\nFound {len(analysis['signals'])} trading signals")
            
            return analysis
            
        except Exception as e:
            print(f"Error in optimize_strategy: {e}")
            traceback.print_exc()
            return {'signals': [], 'indicators': []}

    def analyze_candles(self, df: pd.DataFrame) -> Dict:
        """Analyze OHLC candle patterns and calculate basic indicators"""
        try:
            # Calculate basic indicators using ML agent
            df = self.ml_agent.calculate_indicators(df)
            
            # Prepare features and train model
            X, y, feature_names = self.ml_agent.prepare_features(df)
            
            # Find best features
            best_features = self.ml_agent.find_best_features(X, y, feature_names)
            
            # Generate trading signals
            signals = []
            for i in range(1, len(df)):
                # Example signal generation (you can modify this based on ML predictions)
                if df['RSI_14'].iloc[i] < 30 and df['close'].iloc[i] > df['SMA_50'].iloc[i]:
                    signals.append({
                        'timestamp': df.index[i],
                        'type': 'BUY',
                        'price': df['close'].iloc[i],
                        'reason': 'RSI oversold + Above SMA50'
                    })
                elif df['RSI_14'].iloc[i] > 70 and df['close'].iloc[i] < df['SMA_50'].iloc[i]:
                    signals.append({
                        'timestamp': df.index[i],
                        'type': 'SELL',
                        'price': df['close'].iloc[i],
                        'reason': 'RSI overbought + Below SMA50'
                    })
            
            return {
                'start_price': df['open'].iloc[0],
                'end_price': df['close'].iloc[-1],
                'highest_price': df['high'].max(),
                'lowest_price': df['low'].min(),
                'signals': signals,
                'best_features': best_features
            }
            
        except Exception as e:
            print(f"Error in analyze_candles: {e}")
            traceback.print_exc()
            return {}

    def generate_trades(self, data: pd.DataFrame, analysis: Dict) -> pd.DataFrame:
        """Generate trades based on signals"""
        trades = []
        position = None
        entry_price = 0
        
        for i in range(len(data)):
            current_price = data['close'].iloc[i]
            timestamp = data.index[i]
            
            # Check for signals
            signals = [s for s in analysis['signals'] if s['timestamp'] == timestamp]
            
            for signal in signals:
                if signal['type'] == 'BUY' and position != 'LONG':
                    # Close any existing short position
                    if position == 'SHORT':
                        pnl = entry_price - current_price
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'SELL_CLOSE',
                            'price': current_price,
                            'pnl': pnl
                        })
                    # Open long position
                    position = 'LONG'
                    entry_price = current_price
                    trades.append({
                        'timestamp': timestamp,
                        'type': 'BUY',
                        'price': current_price,
                        'pnl': 0
                    })
                    
                elif signal['type'] == 'SELL' and position != 'SHORT':
                    # Close any existing long position
                    if position == 'LONG':
                        pnl = current_price - entry_price
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'BUY_CLOSE',
                            'price': current_price,
                            'pnl': pnl
                        })
                    # Open short position
                    position = 'SHORT'
                    entry_price = current_price
                    trades.append({
                        'timestamp': timestamp,
                        'type': 'SELL',
                        'price': current_price,
                        'pnl': 0
                    })
        
        return pd.DataFrame(trades)

    def evaluate_signals(self, data: pd.DataFrame, signals: List[Dict]) -> Dict:
        """Evaluate trading signals performance"""
        trades = []
        position = None
        entry_price = 0
        
        for signal in signals:
            timestamp = signal['timestamp']
            price = signal['price']
            
            if signal['type'] == 'BUY':
                if position is None:  # Open long
                    position = 'LONG'
                    entry_price = price
                elif position == 'SHORT':  # Close short and open long
                    pnl = entry_price - price
                    trades.append({
                        'entry_time': timestamp,
                        'exit_time': timestamp,
                        'type': 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': price,
                        'pnl': pnl
                    })
                    position = 'LONG'
                    entry_price = price
                    
            elif signal['type'] == 'SELL':
                if position is None:  # Open short
                    position = 'SHORT'
                    entry_price = price
                elif position == 'LONG':  # Close long and open short
                    pnl = price - entry_price
                    trades.append({
                        'entry_time': timestamp,
                        'exit_time': timestamp,
                        'type': 'LONG',
                        'entry_price': entry_price,
                        'exit_price': price,
                        'pnl': pnl
                    })
                    position = 'SHORT'
                    entry_price = price
        
        # Close any open position at the end
        if position:
            last_price = data['close'].iloc[-1]
            pnl = last_price - entry_price if position == 'LONG' else entry_price - last_price
            trades.append({
                'entry_time': timestamp,
                'exit_time': data.index[-1],
                'type': position,
                'entry_price': entry_price,
                'exit_price': last_price,
                'pnl': pnl
            })
        
        return pd.DataFrame(trades)

if __name__ == "__main__":
    # Create an instance of TradingBacktest
    backtest = TradingBacktest(
        start_date="2024-01-01",
        end_date="2024-03-20",
        timeframe="H1"
    )
    
    # Fetch historical data for XAU_USD (Gold)
    data = backtest.fetch_historical_data("XAU_USD")
    
    if not data.empty:
        print("\nData Overview:")
        print(f"Number of periods: {len(data)}")
        print(f"Date range: {data.index.min()} to {data.index.max()}")
        print("\nPrice Summary:")
        print(f"Starting Price: ${data['open'].iloc[0]:.2f}")
        print(f"Current Price: ${data['close'].iloc[-1]:.2f}")
        print(f"Highest Price: ${data['high'].max():.2f}")
        print(f"Lowest Price: ${data['low'].min():.2f}")
        
        # Run ML analysis
        print("\nRunning ML Strategy Analysis...")
        strategy_results = backtest.optimize_strategy(data)
        
        # Calculate trade performance
        trades_df = backtest.generate_trades(data, strategy_results)
        metrics = backtest.calculate_metrics(trades_df)
        
        # Print detailed report
        backtest.print_performance_report(metrics)
        
        # Save results to CSV
        trades_df.to_csv('backtest_results.csv')
        print("\nResults saved to backtest_results.csv")
    else:
        print("No data received from API")