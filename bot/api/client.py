import time
import threading
import queue
import sqlite3
from typing import List, Dict

class APIClient:
    def __init__(self, db_path: str = "config/market_data.db", batch_size: int = 200, flush_interval: int = 60):
        """
        :param db_path: Path to the local SQLite database file
        :param batch_size: How many items to write to the DB at once
        :param flush_interval: Max time (seconds) to wait before flushing a partial batch
        """
        self.db_path = db_path
        self.queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = True

        self.batches = {} 
        self.last_flush = {}
        
        self._init_db()

        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _init_db(self):
        """Initialize the SQLite database and create the prices table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_prices (
                    unique_name TEXT,
                    server TEXT,
                    item_type TEXT,
                    city TEXT,
                    price INTEGER,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (unique_name, server, item_type, city)
                )
            ''')
            conn.commit()

    def update_item_price(self, unique_name: str, city_key: str, price: int, item_type: str = "fast", server: str = "US"):
        """Queue a price update."""
        self.queue.put({
            "unique_name": unique_name,
            city_key: price,
            "_type": item_type,
            "_server": server
        })

    def _worker_loop(self):
        """Background thread to batch updates and INSERT/UPDATE them in the local DB."""
        while self.running:
            try:
                try:
                    item = self.queue.get(timeout=0.5)
                    
                    i_type = item.pop("_type", "fast")
                    i_server = item.pop("_server", "US")
                    batch_key = (i_server, i_type)

                    if batch_key not in self.batches:
                        self.batches[batch_key] = {}
                        self.last_flush[batch_key] = time.time()
                    
                    u_name = item["unique_name"]
                    
                    if u_name not in self.batches[batch_key]:
                         self.batches[batch_key][u_name] = item
                    else:
                         self.batches[batch_key][u_name].update(item)
                        
                except queue.Empty:
                    pass

                current_time = time.time()
                
                for key in list(self.batches.keys()):
                    server, i_type = key 
                    batch = self.batches[key]
                    
                    is_batch_full = len(batch) >= self.batch_size
                    is_time_up = (current_time - self.last_flush[key] >= self.flush_interval) and len(batch) > 0

                    if is_batch_full or is_time_up:
                        self._save_batch_to_db(list(batch.values()), item_type=i_type, server=server)
                        self.batches[key] = {} # Clear batch
                        self.last_flush[key] = current_time

            except Exception as e:
                print(f"Worker Loop Error: {e}")
                time.sleep(1)

    def force_update(self):
        current_time = time.time()
        for key in list(self.batches.keys()):
            server, i_type = key
            batch = self.batches[key]
            if batch:
                self._save_batch_to_db(list(batch.values()), item_type=i_type, server=server)
                self.batches[key] = {}
                self.last_flush[key] = current_time

    def _save_batch_to_db(self, items: List[Dict], item_type: str, server: str):
        """Transforms the batched data and writes it to the local SQLite database."""
        db_records = []
        
        # Flatten the data structure for SQL
        for item in items:
            u_name = item.pop("unique_name")
            for city_key, price in item.items():
                # Extract actual city name if it includes 'price_' prefix (e.g. 'price_caerleon' -> 'caerleon')
                city = city_key.replace("price_", "") if "price_" in city_key else city_key
                db_records.append((u_name, server, item_type, city, price))

        if not db_records:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO market_prices (unique_name, server, item_type, city, price, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(unique_name, server, item_type, city) 
                    DO UPDATE SET price = excluded.price, updated_at = CURRENT_TIMESTAMP
                ''', db_records)
                conn.commit()
            print(f"Successfully saved {len(items)} items ({item_type}) to local DB for {server}.")
        except Exception as e:
            print(f"SQLite DB error: {e}")

    def stop(self):
        self.running = False
        self.worker_thread.join()
        self.force_update()