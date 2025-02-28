from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, Trade, fetch_oanda_price
import logging

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
