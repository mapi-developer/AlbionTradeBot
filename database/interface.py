from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from .models import Base, MarketOrder
import threading
import queue
from datetime import datetime

# Matches your Docker compose settings
DB_URL = "postgresql://albion_user:albion_password@127.0.0.1:5438/albion_market"

class DatabaseInterface:
    def __init__(self):
        self.engine = create_engine(DB_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.write_queue = queue.Queue()
        self.running = True
        
        self.writer_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.writer_thread.start()

    def add_order(self, order_dict):
        self.write_queue.put(order_dict)

    def _worker_loop(self):
        session = self.Session()
        batch = []
        while self.running:
            try:
                # Wait briefly for new items
                try:
                    item = self.write_queue.get(timeout=1.0)
                    batch.append(item)
                except queue.Empty:
                    pass

                # Process batch if full or if time passed
                if batch:
                    self._process_batch(session, batch)
                    batch = []
            except Exception as e:
                print(f"[DB Error] {e}")

    def _process_batch(self, session, batch_data):
        try:
            stmt = insert(MarketOrder).values([
                {
                    'id': d.get('Id'),
                    'item_id': d.get('ItemTypeId'),
                    'location_id': int(d.get('LocationId') or 0),
                    'quality': d.get('QualityLevel'),
                    'enchantment': d.get('EnchantmentLevel'),
                    'price': d.get('UnitPriceSilver'),
                    'amount': d.get('Amount'),
                    'expires': d.get('Expires'),
                    'raw_data': d
                }
                for d in batch_data if d.get('Id') is not None
            ])
            
            # Update price if order exists
            do_update = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={'price': stmt.excluded.price, 'amount': stmt.excluded.amount, 'ingested_at': datetime.utcnow()}
            )
            
            session.execute(do_update)
            session.commit()
            print(f"[DB] Saved {len(batch_data)} orders")
        except Exception as e:
            print(f"[DB Write Error] {e}")
            session.rollback()