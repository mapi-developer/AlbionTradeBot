import requests
import json
import os

ITEMS_JSON_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json"
CACHE_FILE = "items.json"

class ItemManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ItemManager, cls).__new__(cls)
            cls._instance.id_to_name = {}
            cls._instance.load_items()
        return cls._instance

    def load_items(self):
        # Check if we have a local cache
        if not os.path.exists(CACHE_FILE):
            print("Downloading Item Database (this happens once)...")
            try:
                response = requests.get(ITEMS_JSON_URL)
                response.raise_for_status()
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    f.write(response.text)
            except Exception as e:
                print(f"Failed to download items: {e}")
                return

        # Load into memory
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # Map "Index" (int) to "UniqueName" (string)
                    if "Index" in item and "UniqueName" in item:
                        # Indexes in JSON are often strings, convert to int
                        idx = int(item["Index"])
                        self.id_to_name[idx] = item["UniqueName"]
            print(f"[ItemManager] Loaded {len(self.id_to_name)} items.")
        except Exception as e:
            print(f"[ItemManager] Error loading cache: {e}")

    def get_name(self, item_id):
        return self.id_to_name.get(item_id, str(item_id)) # Fallback to ID if unknown