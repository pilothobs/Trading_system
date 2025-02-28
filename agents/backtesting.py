from typing import Dict, List
import pandas as pd
from fastapi import FastAPI
import requests
from datetime import datetime, timedelta

class TradingBacktest:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.trades: List[Dict] = []
        self.results = {
            'crew_pnl': [],
            'langgraph_pnl': [],
            'combined_pnl': []
        }

    def fetch_historical_data(self, symbol: str) -> pd.DataFrame:
        """Fetch historical data from OANDA via FastAPI"""
        try:
            url = f"http://localhost:8000/historical/{symbol}"
            params = {
                'start_date': self.start_date,
                'end_date': self.end_date
            }
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}")
                print(f"Response: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            
            # Debug print
            print("Received data:", data)
            
            # Ensure data is in the correct format for DataFrame
            if not isinstance(data, list):
                print("Error: Expected list of records from API")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return pd.DataFrame()

    def run_crew_analysis(self, data: pd.DataFrame):
        # Import your crew_agents.py logic here
        pass

    def run_langgraph_analysis(self, data: pd.DataFrame):
        # Import your prim_gpt.py logic here
        pass

    def calculate_metrics(self):
        df = pd.DataFrame(self.trades)
        return {
            'total_pnl': df['pnl'].sum(),
            'max_drawdown': self.calculate_drawdown(df['pnl']),
            'win_rate': len(df[df['pnl'] > 0]) / len(df),
            'sharpe_ratio': self.calculate_sharpe(df['pnl'])
        }

    @staticmethod
    def calculate_drawdown(pnl_series: pd.Series) -> float:
        cumulative = pnl_series.cumsum()
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        return abs(drawdown.min())

    @staticmethod
    def calculate_sharpe(pnl_series: pd.Series) -> float:
        return pnl_series.mean() / pnl_series.std() * (252 ** 0.5)  # Annualized

if __name__ == "__main__":
    # Create an instance of TradingBacktest
    backtest = TradingBacktest(
        start_date="2024-01-01",
        end_date="2024-03-20"
    )
    
    # Fetch some historical data
    data = backtest.fetch_historical_data("EUR_USD")
    print("Historical data shape:", data.shape)
    
    # Run analyses
    backtest.run_crew_analysis(data)
    backtest.run_langgraph_analysis(data)
    
    # Calculate and print metrics
    metrics = backtest.calculate_metrics()
    print("\nBacktest Results:")
    for metric, value in metrics.items():
        print(f"{metric}: {value}")
