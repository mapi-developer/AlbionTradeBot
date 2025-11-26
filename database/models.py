from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class MarketOrder(Base):
    __tablename__ = 'market_orders'

    # Primary Key
    id = Column(BigInteger, primary_key=True) # The Game's Order ID
    
    # Core Data (Indexed for fast querying)
    item_id = Column(String, index=True)
    location_id = Column(Integer, index=True)
    quality = Column(Integer)
    enchantment = Column(Integer)
    
    # Market Data
    price = Column(BigInteger)
    amount = Column(Integer)
    expires = Column(String)
    
    # Metadata
    ingested_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Data Lake - Store the full raw packet just in case we missed a field
    raw_data = Column(JSON)

    def __repr__(self):
        return f"<Order(item={self.item_id}, price={self.price})>"