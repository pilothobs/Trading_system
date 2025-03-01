from database import SessionLocal, Trade, Base, engine
from datetime import datetime, timedelta
import random

def populate_historical_data():
    # Create fresh tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Generate trades for the past 3 months
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 20)
        current_date = start_date
        
        # Simulate Gold price starting at $2000
        current_price = 2000.0
        
        while current_date <= end_date:
            # Simulate price movement (random walk with drift)
            price_change = random.normalvariate(0.5, 5.0)  # Mean: $0.5, Std: $5.0
            current_price += price_change
            
            # Create both BUY and SELL trades
            trade_types = ['BUY', 'SELL']
            for trade_type in trade_types:
                trade = Trade(
                    symbol='XAU_USD',
                    trade_type=trade_type,
                    amount=1,  # 1 oz of gold
                    price=round(current_price, 2),
                    created_at=current_date
                )
                db.add(trade)
            
            # Move to next hour
            current_date += timedelta(hours=1)
        
        db.commit()
        print("Database populated successfully!")
        
        # Print some statistics
        trade_count = db.query(Trade).count()
        print(f"Total trades created: {trade_count}")
        
        first_trade = db.query(Trade).order_by(Trade.created_at).first()
        last_trade = db.query(Trade).order_by(Trade.created_at.desc()).first()
        print(f"\nDate range: {first_trade.created_at} to {last_trade.created_at}")
        print(f"Price range: ${first_trade.price:.2f} to ${last_trade.price:.2f}")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_historical_data() 