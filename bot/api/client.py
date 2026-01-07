import time
import threading
import queue
import requests
from typing import List, Dict


class APIClient:
    def __init__(self, api_url: str, batch_size: int = 200, flush_interval: int = 120):
        """
        :param api_url: The URL of your Cloud Run service
        :param batch_size: How many items to send in one HTTP request
        :param flush_interval: Max time (seconds) to wait before sending a partial batch
        """
        self.api_url = api_url.rstrip("/")
        self.queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = True

        self.batches = {
            "fast": {},
            "order": {}
        }
        self.last_flush = {
            "fast": time.time(),
            "order": time.time()
        }
        
        # Start the background worker
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def update_item_price(self, unique_name: str, city_key: str, price: int, item_type: str = "fast"):
        """
        Queue a price update.
        :param item_type: 'fast' or 'order' (matches backend API)
        :param city_key: e.g. 'price_caerleon'
        """
        # Add to queue with a special key for routing
        self.queue.put({
            "unique_name": unique_name,
            city_key: price,
            "_type": item_type 
        })

    def _worker_loop(self):
        """Background thread to batch updates and POST them to the API."""
        # Separate  self.batches for Fast and Order items

        while self.running:
            try:
                # 1. Dequeue and Sort
                try:
                    item = self.queue.get(timeout=0.5)
                    
                    # Extract type (default to 'fast' if missing)
                    i_type = item.pop("_type", "fast")
                    if i_type not in  self.batches:
                        i_type = "fast"
                    
                    u_name = item["unique_name"]
                    
                    # Merge logic for the specific batch
                    if u_name not in  self.batches[i_type]:
                         self.batches[i_type][u_name] = item
                    else:
                         self.batches[i_type][u_name].update(item)
                        
                except queue.Empty:
                    pass

                # 2. Check Flush Conditions for each type
                current_time = time.time()
                
                for t in ["fast", "order"]:
                    batch =  self.batches[t]
                    is_batch_full = len(batch) >= self.batch_size
                    is_time_up = (current_time - self.last_flush[t] >= self.flush_interval) and len(batch) > 0

                    if is_batch_full or is_time_up:
                        self._send_batch(list(batch.values()), item_type=t)
                        self.batches[t] = {} # Clear batch
                        self.last_flush[t] = current_time

            except Exception as e:
                print(f"Worker Loop Error: {e}")
                time.sleep(1)

    def force_update(self):
        current_time = time.time()
        for t in ["fast", "order"]:
            batch =  self.batches[t]
            self._send_batch(list(batch.values()), item_type=t)
            self.batches[t] = {} # Clear batch
            self.last_flush[t] = current_time

    def _send_batch(self, items: List[Dict], item_type: str):
        """Sends the HTTP PUT request to the backend with the correct type parameter."""
        try:
            endpoint = f"{self.api_url}/items/prices"
            
            # Updated to pass 'type' as a query parameter
            response = requests.put(
                endpoint, 
                json=items, 
                params={"type": item_type}, 
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Successfully synced {len(items)} items ({item_type}).")
            else:
                print(f"Failed to sync items ({item_type}): {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"HTTP Connection error: {e}")

    def stop(self):
        """Gracefully stop the worker."""
        self.running = False
        self.worker_thread.join()