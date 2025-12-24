from sqlalchemy import BigInteger, String, DateTime, Integer, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
from datetime import datetime


class Base(DeclarativeBase):
    pass


class ItemData(Base):
    __tablename__ = "Item"

    unique_name: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    
    price_black_market: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_caerleon: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_lymhurst: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_bridgewatch: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_fort_sterling: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_thetford: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_martlock: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)
    price_brecilien: Mapped[Optional[BigInteger]] = mapped_column(BigInteger)

    black_market_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    caerleon_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    lymhurst_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    bridgewatch_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fort_sterling_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    thetford_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    martlock_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    brecilien_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )


class MarketOrder(Base):
    __tablename__ = 'market_orders'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_db_name: Mapped[str] = mapped_column(String, index=True) 
    auction_type: Mapped[Optional[str]] = mapped_column(String)
    location_id: Mapped[int] = mapped_column(Integer, index=True)
    quality: Mapped[int] = mapped_column(Integer)
    enchantment: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[int] = mapped_column(Integer)
    expires: Mapped[Optional[str]] = mapped_column(String)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)

class MarketHistory(Base):
    __tablename__ = 'market_history'
    
    item_db_name: Mapped[str] = mapped_column(String, primary_key=True)
    quality: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[int] = mapped_column(BigInteger, primary_key=True) 
    aggregation_type: Mapped[int] = mapped_column(Integer, primary_key=True) 
    
    item_amount: Mapped[int] = mapped_column(BigInteger)
    silver_amount: Mapped[int] = mapped_column(BigInteger)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())