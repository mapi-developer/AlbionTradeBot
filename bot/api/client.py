import time
import threading
import queue
import requests
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AlbionBotClient")

class APIClient:
    def __init__(self, api_url: str, batch_size: int = 200, flush_interval: int = 120):
        """
        :param api_url: The URL of your Cloud Run service (e.g. https://trade-backend...run.app)
        :param batch_size: How many items to send in one HTTP request
        :param flush_interval: Max time (seconds) to wait before sending a partial batch
        """
        self.api_url = api_url.rstrip("/")
        self.queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = True
        
        # Start the background worker
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def update_item_price(self, unique_name: str, city: str, price: int):
        """
        Queue a price update.
        City should be 'Caerleon', 'Martlock', etc. Case insensitive.
        """
        
        # 2. Add to queue
        self.queue.put({
            "unique_name": unique_name,
            city: price
        })

    def _worker_loop(self):
        """Background thread to batch updates and POST them to the API."""
        batch = {}
        last_flush = time.time()

        while self.running:
            try:
                # Attempt to get an item from queue with a short timeout
                try:
                    item = self.queue.get(timeout=0.5)
                    
                    # Merge logic: If we have multiple updates for the same item in the buffer, merge them
                    u_name = item["unique_name"]
                    if u_name not in batch:
                        batch[u_name] = item
                    else:
                        batch[u_name].update(item)
                        
                except queue.Empty:
                    pass

                # Check if we should flush
                current_time = time.time()
                is_batch_full = len(batch) >= self.batch_size
                is_time_up = (current_time - last_flush >= self.flush_interval) and len(batch) > 0

                if is_batch_full or is_time_up:
                    self._send_batch(list(batch.values()))
                    batch = {}
                    last_flush = current_time

            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(1)

    def _send_batch(self, items: List[Dict]):
        """Sends the HTTP PUT request to the backend."""
        try:
            # Your main.py endpoint is PUT /items/prices
            endpoint = f"{self.api_url}/items/prices"
            
            response = requests.put(endpoint, json=items, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully synced {len(items)} items. Backend buffer size: {response.json().get('buffer_size')}")
            else:
                logger.error(f"Failed to sync items: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"HTTP Connection error: {e}")

    def stop(self):
        """Gracefully stop the worker."""
        self.running = False
        self.worker_thread.join()