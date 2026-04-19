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

        # FIXED: Initialize as empty. Keys will be tuples: (server, type)
        self.batches = {} 
        self.last_flush = {}
        
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def update_item_price(self, unique_name: str, city_key: str, price: int, item_type: str = "fast", server: str = "US"):
        """
        Queue a price update.
        :param item_type: 'fast' or 'order' (matches backend API)
        :param city_key: e.g. 'price_caerleon'
        :param server: 'US', 'EU', or 'AS'
        """
        self.queue.put({
            "unique_name": unique_name,
            city_key: price,
            "_type": item_type,
            "_server": server
        })

    def _worker_loop(self):
        """Background thread to batch updates and POST them to the API."""
        while self.running:
            try:
                try:
                    item = self.queue.get(timeout=0.5)
                    
                    i_type = item.pop("_type", "fast")
                    i_server = item.pop("_server", "US")
                    
                    # Create tuple key (Server, Type)
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
                
                # Iterate over keys (which are now tuples)
                for key in list(self.batches.keys()):
                    server, i_type = key 
                    batch = self.batches[key]
                    
                    is_batch_full = len(batch) >= self.batch_size
                    is_time_up = (current_time - self.last_flush[key] >= self.flush_interval) and len(batch) > 0

                    if is_batch_full or is_time_up:
                        self._send_batch(list(batch.values()), item_type=i_type, server=server)
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
                self._send_batch(list(batch.values()), item_type=i_type, server=server)
                self.batches[key] = {}
                self.last_flush[key] = current_time

    def _send_batch(self, items: List[Dict], item_type: str, server: str):
        """Sends the HTTP PUT request to the backend with the correct type and server parameters."""
        try:
            endpoint = f"{self.api_url}/items/prices"
            
            response = requests.put(
                endpoint, 
                json=items, 
                params={"type": item_type, "server": server}, 
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Successfully synced {len(items)} items ({item_type}) for {server}.")
            else:
                print(f"Failed to sync items ({item_type}) for {server}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"HTTP Connection error: {e}")

    def stop(self):
        self.running = False
        self.worker_thread.join()