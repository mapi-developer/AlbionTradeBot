from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from .models import Base, MarketOrder
import threading
import queue
from datetime import datetime

# Database Config
DB_URL = "postgresql://albion_user:albion_password@localhost:5432/albion_market"

class DatabaseInterface:
    def __init__(self):
        self.engine = create_engine(DB_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # A queue to decouple sniffing from writing
        self.write_queue = queue.Queue()
        self.running = True
        
        # Start the background writer
        self.writer_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.writer_thread.start()

    def add_order(self, order_dict):
        """Sniffer calls this. It returns instantly."""
        self.write_queue.put(order_dict)

    def _worker_loop(self):
        """Background thread that creates DB sessions and inserts data."""
        session = self.Session()
        batch = []
        
        print("[DB] Worker started.")
        
        while self.running:
            try:
                # Get item from queue (wait up to 1 second)
                item = self.write_queue.get(timeout=1.0)
                batch.append(item)
                
                # If batch is full, write it
                if len(batch) >= 100:
                    self._process_batch(session, batch)
                    batch = []
                    
            except queue.Empty:
                # If queue is empty but we have items in batch, write them now
                if batch:
                    self._process_batch(session, batch)
                    batch = []
                continue
            except Exception as e:
                print(f"[DB Error] {e}")

    def _process_batch(self, session, batch_data):
        """
        Uses Postgres 'UPSERT' (Insert on Conflict) logic.
        If we see the same Order ID again, we update the data.
        """
        try:
            # Prepare data for SQLAlchemy
            insert_stmt = insert(MarketOrder).values([
                {
                    'id': d.get('Id'),
                    'item_id': d.get('ItemTypeId'),
                    'location_id': int(d.get('LocationId', 0) or 0),
                    'quality': d.get('QualityLevel'),
                    'enchantment': d.get('EnchantmentLevel'),
                    'price': d.get('UnitPriceSilver'),
                    'amount': d.get('Amount'),
                    'expires': d.get('Expires'),
                    'raw_data': d
                }
                for d in batch_data if d.get('Id') is not None
            ])

            # On conflict (same Order ID), do nothing (or update if you prefer)
            do_update = insert_stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'amount': insert_stmt.excluded.amount,
                    'price': insert_stmt.excluded.price,
                    'ingested_at': datetime.utcnow()
                }
            )

            session.execute(do_update)
            session.commit()
            print(f"[DB] Saved {len(batch_data)} orders.")
            
        except Exception as e:
            print(f"[DB Write Error] {e}")
            session.rollback()