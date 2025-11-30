from sqlalchemy import Column, Integer, String, BigInteger, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MarketOrder(Base):
    __tablename__ = 'market_orders'
    id = Column(BigInteger, primary_key=True)
    item_db_name = Column(String, index=True) 
    auction_type = Column(String)
    location_id = Column(Integer, index=True)
    quality = Column(Integer)
    enchantment = Column(Integer)
    price = Column(BigInteger)
    amount = Column(Integer)
    expires = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(JSON)

class MarketHistory(Base):
    __tablename__ = 'market_history'
    
    # Composite Primary Key
    item_db_name = Column(String, primary_key=True)
    quality = Column(Integer, primary_key=True)
    location_id = Column(Integer, primary_key=True)
    timestamp = Column(BigInteger, primary_key=True) 
    aggregation_type = Column(Integer, primary_key=True) 
    
    item_amount = Column(BigInteger)
    silver_amount = Column(BigInteger)
    ingested_at = Column(DateTime, default=datetime.utcnow)

class ItemData(Base):
    __tablename__ = 'items_data'

    unique_name = Column(String, primary_key=True)
    price_black_market = Column(BigInteger, default=0)
    price_caerleon = Column(BigInteger, default=0)
    price_lymhurst = Column(BigInteger, default=0)
    price_bridgewatch = Column(BigInteger, default=0)
    price_fort_sterling = Column(BigInteger, default=0)
    price_thetford = Column(BigInteger, default=0)
    price_martlock = Column(BigInteger, default=0)
    black_market_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    caerleon_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lymhurst_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    bridgewatch_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fort_sterling_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    thetford_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    martlock_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
