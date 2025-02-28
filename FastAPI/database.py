from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path, override=True)

# OANDA API Credentials
OANDA_API_URL = os.getenv("OANDA_API_URL")
OANDA_API_KEY = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")

# Database setup (SQLite for now)
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Trade Model
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    trade_type = Column(String)
    amount = Column(Integer)
    price = Column(Float)

# Create tables if they don’t exist
Base.metadata.create_all(bind=engine)

# Fetch Market Price from OANDA
def fetch_oanda_price(symbol):
    """Fetches the latest market price from OANDA"""
    oanda_symbol = symbol.replace("/", "_")  # Ensure correct OANDA format

    url = f"{OANDA_API_URL}/accounts/{OANDA_ACCOUNT_ID}/pricing?instruments={oanda_symbol}"
    headers = {"Authorization": f"Bearer {OANDA_API_KEY}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        prices = data.get("prices", [])
        if prices:
            return float(prices[0]["bids"][0]["price"])  # Return bid price
        else:
            return None
    else:
        print(f"Error fetching OANDA data: {response.status_code}, {response.text}")
        return None
