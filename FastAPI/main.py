from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, Trade, fetch_oanda_price
import logging
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OANDA_API_KEY = os.getenv("OANDA_API_KEY")
OANDA_API_URL = os.getenv("OANDA_API_URL")

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI is working!"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/trade/")
def create_trade(symbol: str, trade_type: str, amount: int, db: Session = Depends(get_db)):
    print(f"🔹 Received trade request: {symbol}, {trade_type}, {amount}")
    
    price = fetch_oanda_price(symbol)
    if price is None:
        return {"error": "Failed to fetch market price from OANDA"}
    
    trade = Trade(symbol=symbol, trade_type=trade_type, amount=amount, price=price)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    print(f"✅ Trade created: {trade.id}")
    return trade

@app.get("/trades/")
def read_trades(db: Session = Depends(get_db)):
    return db.query(Trade).all()

@app.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str, 
    start_date: str, 
    end_date: str, 
    timeframe: str = "H1",
    db: Session = Depends(get_db)
):
    try:
        # Validate timeframe
        valid_timeframes = ["S5", "S10", "S15", "S30", 
                          "M1", "M2", "M4", "M5", "M10", "M15", "M30",
                          "H1", "H2", "H3", "H4", "H6", "H8", "H12",
                          "D", "W", "M"]
        if timeframe not in valid_timeframes:
            raise HTTPException(status_code=400, detail=f"Invalid timeframe. Must be one of: {valid_timeframes}")

        # Format OANDA API URL
        instrument = symbol.replace("/", "_")
        url = f"{OANDA_API_URL}/instruments/{instrument}/candles"
        
        params = {
            "from": start_date + "T00:00:00Z",
            "to": end_date + "T23:59:59Z",
            "granularity": timeframe,
            "price": "MBA"  # Midpoint, Bid, and Ask prices
        }
        
        headers = {
            "Authorization": f"Bearer {OANDA_API_KEY}",
            "Content-Type": "application/json"
        }

        # Fetch data from OANDA
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logging.error(f"OANDA API Error: {response.text}")
            raise HTTPException(status_code=response.status_code, 
                              detail=f"OANDA API Error: {response.text}")

        candles = response.json().get("candles", [])
        
        # Transform candles into our format
        historical_data = []
        for candle in candles:
            if candle["complete"]:  # Only use completed candles
                historical_data.append({
                    "timestamp": candle["time"],
                    "open": float(candle["mid"]["o"]),
                    "high": float(candle["mid"]["h"]),
                    "low": float(candle["mid"]["l"]),
                    "close": float(candle["mid"]["c"]),
                    "volume": candle["volume"]
                })

        return historical_data

    except Exception as e:
        logging.error(f"Error fetching historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
