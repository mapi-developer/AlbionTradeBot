from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from .models import Base, MarketHistory, MarketOrder
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

    def add_history(self, history_list):
        """
        Expects a list of dicts:
        [{'item_id': 'T4_BAG', 'location_id': 3005, 'quality': 1, 
          'timestamp': 12345678, 'item_amount': 10, 'silver_amount': 5000, 
          'aggregation_type': '24'}]
        """
        self.write_queue.put(('history', history_list))

    # Update _process_batch to handle tuple types
    def _worker_loop(self):
        session = self.Session()
        batch_orders = []
        batch_history = []
        
        while self.running:
            try:
                # Fetch Item
                item_type, item_data = self.write_queue.get(timeout=1.0)
                
                if item_type == 'order':
                    batch_orders.append(item_data)
                elif item_type == 'history':
                    batch_history.extend(item_data) # History comes as a list
                
                # Flush if full
                if len(batch_orders) >= 100:
                    self._process_orders(session, batch_orders)
                    batch_orders = []
                if len(batch_history) >= 100:
                    self._process_history(session, batch_history)
                    batch_history = []
                    
            except queue.Empty:
                # Flush remaining
                if batch_orders: self._process_orders(session, batch_orders)
                if batch_history: self._process_history(session, batch_history)
                batch_orders = []
                batch_history = []
    
    # Rename original _process_batch to _process_orders
    def _process_orders(self, session, batch_data):
        # ... (Existing Order Insert Logic) ...
        pass

    def _process_history(self, session, batch_data):
        try:
            # Postgres Upsert for History
            from sqlalchemy.dialects.postgresql import insert
            stmt = insert(MarketHistory).values(batch_data)
            
            do_update = stmt.on_conflict_do_update(
                index_elements=['item_id', 'location_id', 'quality', 'timestamp'],
                set_={'item_amount': stmt.excluded.item_amount, 'silver_amount': stmt.excluded.silver_amount}
            )
            session.execute(do_update)
            session.commit()
            print(f"[DB] Saved {len(batch_data)} history records")
        except Exception as e:
            print(f"[DB History Error] {e}")
            session.rollback()