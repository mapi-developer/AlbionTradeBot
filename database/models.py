from sqlalchemy import Column, Integer, String, BigInteger, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MarketOrder(Base):
    __tablename__ = 'market_orders'

    id = Column(BigInteger, primary_key=True)
    item_id = Column(String, index=True)
    location_id = Column(Integer, index=True)
    quality = Column(Integer)
    enchantment = Column(Integer)
    price = Column(BigInteger)
    amount = Column(Integer)
    expires = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow, index=True)
    raw_data = Column(JSON)

class MarketHistory(Base):
    __tablename__ = 'market_history'

    # Composite Primary Key: Item + Quality + Location + Timestamp
    item_id = Column(String, primary_key=True)
    location_id = Column(Integer, primary_key=True)
    quality = Column(Integer, primary_key=True)
    timestamp = Column(BigInteger, primary_key=True) # Epoch time from game
    
    aggregation_type = Column(String) # "1", "24" (hours/days)
    item_amount = Column(BigInteger)
    silver_amount = Column(BigInteger)
    ingested_at = Column(DateTime, default=datetime.utcnow)