import requests
import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
LIMEX_API_KEY = os.getenv("LIMEX_API_KEY")  # Set this in your .env file
LIMEX_API_URL = "https://hub.limex.com/v1/candles/"  # Update as needed

# SQLite database setup
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define MarketData model
class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(String)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)

# Create database table
Base.metadata.create_all(bind=engine)

# Function to fetch market data from Limex API
def fetch_limex_data(symbol: str, timeframe: str = "1h"):
    headers = {"Authorization": f"Bearer {LIMEX_API_KEY}"}
    params = {"symbol": symbol, "timeframe": timeframe}
    
    response = requests.get(LIMEX_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

# Function to store fetched data in SQLite
def store_market_data(data, symbol):
    db = SessionLocal()
    
    for candle in data:
        new_entry = MarketData(
            symbol=symbol,
            timestamp=candle["timestamp"],
            open_price=candle["open"],
            high_price=candle["high"],
            low_price=candle["low"],
            close_price=candle["close"],
            volume=candle["volume"]
        )
        db.add(new_entry)
    
    db.commit()
    db.close()
