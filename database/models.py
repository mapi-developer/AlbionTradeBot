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