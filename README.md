# AI Trading System

An advanced machine learning-powered trading system that analyzes multiple timeframes and hundreds of technical indicators to develop optimal trading strategies.

## 🚀 Features

### Implemented Features
- Multi-timeframe analysis (H1 to Daily)
- Integration with OANDA API for historical data
- FastAPI backend with SQLite database
- Backtesting engine with detailed performance metrics
- Technical indicator analysis
- Machine Learning strategy optimization
- Performance metrics calculation (Win rate, P&L, Sharpe ratio)
- Automated data fetching and processing
- Real-time market data analysis

### Planned Features
- GPU acceleration for faster analysis
- Deep Learning pattern recognition
- Automated strategy optimization
- Risk management system
- Real-time trade execution
- Performance dashboard
- Multiple asset support
- Portfolio optimization
- Advanced ML model selection

## 📊 Project Structure

trading_system/
├── .env                  # Environment variables (API keys)
├── .gitignore           # Git ignore file
├── FastAPI/             # FastAPI server
│   ├── main.py         # Main API application
│   ├── database.py     # Database models and connection
│   └── requirements.txt
├── agents/             # Trading agents
│   ├── backtesting.py # Backtesting engine
│   ├── ml_strategy_agent.py  # ML strategy implementation
│   └── risk_manager.py # Risk management (planned)
├── alembic/            # Database migrations
├── tests/             # Unit tests (planned)
├── docs/              # Documentation (planned)
└── requirements.txt    # Project dependencies

## 🛠️ Installation

### Prerequisites
- Python 3.12+
- pip
- Virtual environment

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trading_system.git
cd trading_system
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate    # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
OANDA_API_KEY=your_api_key
OANDA_ACCOUNT_ID=your_account_id
OANDA_API_URL=https://api-fxtrade.oanda.com/v3
```

## 🚦 Usage

### Starting the System

1. Start FastAPI server:
```bash
cd FastAPI
uvicorn main:app --reload
```

2. Run backtesting:
```bash
cd agents
python backtesting.py
```

### Current Implementation Details

#### FastAPI Backend
- Historical data endpoint (/historical/{symbol})
- SQLite database for data persistence
- OANDA API integration for real-time data
- Error handling and logging

#### Backtesting Engine
- Fetches historical data from OANDA
- Calculates technical indicators
- Implements ML-based trading strategy
- Generates detailed performance reports
- Saves results to CSV for analysis

#### Machine Learning Strategy
- Feature engineering from technical indicators
- Model training and validation
- Signal generation based on ML predictions
- Performance optimization

## 📈 Performance Metrics

The system currently calculates:
- Win rate
- Total P&L
- Profit factor
- Maximum drawdown
- Sharpe ratio
- Sortino ratio
- Monthly analysis
  - Average monthly profit
  - Monthly profit standard deviation
  - Profitable months ratio

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:
- Architecture Overview
- API Reference
- Trading Strategies
- ML Model Details
- Performance Analysis

## ⚠️ Disclaimer

This is experimental software for research purposes only. No financial advice is provided. Use at your own risk.

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read our Contributing Guidelines first.
