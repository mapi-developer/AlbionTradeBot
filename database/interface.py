from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from .models import Base, MarketOrder, MarketHistory
import threading
import queue
from datetime import datetime

# Use port 5438 as configured previously
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
        self.write_queue.put(('order', order_dict))

    def add_history(self, history_list):
        self.write_queue.put(('history', history_list))

    def _worker_loop(self):
        session = self.Session()
        batch_orders = []
        batch_history = []
        
        while self.running:
            try:
                try:
                    # Get data type and payload
                    dtype, data = self.write_queue.get(timeout=1.0)
                    if dtype == 'order':
                        batch_orders.append(data)
                    elif dtype == 'history':
                        batch_history.extend(data)
                except queue.Empty:
                    pass

                if len(batch_orders) >= 5:
                    self._process_orders(session, batch_orders)
                    batch_orders = []
                
                if len(batch_history) >= 5:
                    self._process_history(session, batch_history)
                    batch_history = []

            except Exception as e:
                print(f"[DB Loop Error] {e}")

    def _process_orders(self, session, batch):
        try:
            stmt = insert(MarketOrder).values([
                {
                    'id': d.get('Id'),
                    'item_db_name': d.get('item_db_name'), # New Field
                    'location_id': d.get('LocationId', 0),
                    'quality': d.get('QualityLevel'),
                    'enchantment': d.get('EnchantmentLevel'),
                    'price': d.get('UnitPriceSilver'),
                    'amount': d.get('Amount'),
                    'expires': d.get('Expires'),
                    'raw_data': d
                }
                for d in batch if d.get('Id')
            ])
            # This ensures PRICES UPDATE if the order ID exists
            do_update = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={'price': stmt.excluded.price, 'amount': stmt.excluded.amount, 'ingested_at': datetime.utcnow()}
            )
            session.execute(do_update)
            session.commit()
            print(f"[DB] Saved {len(batch)} orders")
        except Exception as e:
            print(f"[DB Order Error] {e}")
            session.rollback()

    def _process_history(self, session, batch):
        try:
            stmt = insert(MarketHistory).values(batch)
            # This ensures HISTORY UPDATES if data for that time exists
            do_update = stmt.on_conflict_do_update(
                index_elements=['item_db_name', 'quality', 'location_id', 'timestamp', 'aggregation_type'],
                set_={'item_amount': stmt.excluded.item_amount, 'silver_amount': stmt.excluded.silver_amount}
            )
            session.execute(do_update)
            session.commit()
            print(f"[DB] Saved {len(batch)} history records")
        except Exception as e:
            print(f"[DB History Error] {e}")
            session.rollback()