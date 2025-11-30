from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from .models import Base, MarketOrder, MarketHistory, ItemData
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

    def add_mail(self, mail_dict):
        self.write_queue.put(('mail', mail_dict))

    def update_item_prices(self, price_data_list):
        """
        Accepts a list of dicts to update the items_data table.
        Example: [{'unique_name': 'T4_BAG', 'price_caerleon': 50000}]
        """
        self.write_queue.put(('item_data', price_data_list))

    def _worker_loop(self):
        session = self.Session()
        batch_orders = []
        batch_history = []
        batch_mail = []
        batch_item_data = []
        
        while self.running:
            try:
                try:
                    dtype, data = self.write_queue.get(timeout=1.0)
                    if dtype == 'order':
                        batch_orders.append(data)
                    elif dtype == 'history':
                        batch_history.extend(data)
                    elif dtype == 'mail':
                        batch_mail.append(data)
                    elif dtype == 'item_data':
                        batch_item_data.extend(data)
                except queue.Empty:
                    pass

                if len(batch_orders) >= 5:
                    self._process_orders(session, batch_orders)
                    batch_orders = []
                
                if len(batch_history) >= 5:
                    self._process_history(session, batch_history)
                    batch_history = []
                
                if len(batch_mail) >= 1: # Process mail immediately
                    self._process_mail(session, batch_mail)
                    batch_mail = []

                if len(batch_item_data) >= 1:
                    self._process_item_data(session, batch_item_data)
                    batch_item_data = []

            except Exception as e:
                print(f"[DB Loop Error] {e}")

    def _process_orders(self, session, batch):
        try:
            stmt = insert(MarketOrder).values([
                {
                    'id': d.get('Id'),
                    'item_db_name': d.get('item_db_name'),
                    'auction_type': d.get('AuctionType'),
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

    def _process_item_data(self, session, batch):
        try:
            for data in batch:
                if 'unique_name' not in data:
                    continue
                
                # Create the insert statement
                stmt = insert(ItemData).values(data)
                
                # We dynamically construct the SET clause to only update columns provided in the input.
                # This ensures if we send {'unique_name': 'X', 'price_caerleon': 1}, we don't wipe out 'price_lymhurst'.
                update_cols = {
                    col: getattr(stmt.excluded, col)
                    for col in data.keys()
                    if col != 'unique_name'
                }
                update_cols['updated_at'] = datetime.utcnow()

                do_update = stmt.on_conflict_do_update(
                    index_elements=['unique_name'],
                    set_=update_cols
                )
                session.execute(do_update)

            session.commit()
            print(f"[DB] Updated item data for {len(batch)} items")
        except Exception as e:
            print(f"[DB ItemData Error] {e}")
            session.rollback()