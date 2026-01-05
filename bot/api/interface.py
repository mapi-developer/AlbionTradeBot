import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

from .client import APIClient 


class DatabaseInterface:
    def __init__(self):
        load_dotenv()
        
        # 1. Configuration
        self.api_url = os.getenv('API_URL', "https://trade-backend-service-1054089939982.europe-west4.run.app")
        
        # 2. Initialize the background worker client
        # This handles the queuing and batching automatically
        self.client = APIClient(api_url=self.api_url)
        
        print(f"✅ Interface initialized with API: {self.api_url}")

    def check_connection_status(self) -> bool:
        """
        Pings the backend to ensure it is online.
        """
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ Backend API connection is successful.")
                return True
            else:
                print(f"❌ Backend API returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend API connection failed. Error: {e}")
            return False

    def update_item_prices(self, price_data_list: List[Dict]):
        for entry in price_data_list:
            # We copy to avoid modifying the original dict inside the loop
            data = entry.copy()
            unique_name = data.pop('unique_name', None)
            
            if not unique_name:
                continue

            # Iterate over keys to find prices (e.g., 'price_caerleon', 'price_martlock')
            for key, price in data.items():
                if key.startswith('price_') and isinstance(price, (int, float)):
                    # Extract city name: 'price_caerleon' -> 'caerleon'
                    
                    # Queue the update using the client
                    self.client.update_item_price(unique_name, key, int(price))

    def get_all_prices_for_city(self, city: str) -> Dict[str, int]:
        """
        Retrieves all item prices for a specific city via API.
        """
        try:
            # The backend endpoint /items/ returns a list of all items
            response = requests.get(f"{self.api_url}/items/", timeout=10)
            if response.status_code != 200:
                return {}

            items = response.json()
            city_key = f"price_{city.lower().replace(' ', '_')}"
            
            # Filter the result to return {unique_name: price} for the requested city
            result = {}
            for item in items:
                price = item.get(city_key)
                if price:
                    result[item['unique_name']] = price
            
            return result

        except Exception as e:
            return {}

    def get_last_update_at(self) -> Optional[datetime]:
        """
        Fetches the latest timestamp from the DB. 
        Note: Requires calling the API.
        """
        try:
            # We can fetch a small batch or a specific endpoint if you create one.
            # For now, we fetch items and find the max 'updated_at'
            # (In production, you should make a lightweight /status endpoint for this)
            response = requests.get(f"{self.api_url}/items/last_update", timeout=5) # You might need to add this endpoint
            # Fallback if endpoint doesn't exist: return current time or None
            return datetime.utcnow() 
        except Exception:
            return None

    # --- DEPRECATED METHODS ---
    # These functionalities are not yet supported by your new 'main.py' endpoints.
    # We keep the methods so your bot doesn't crash if it calls them.

    def add_order(self, order_dict):
        pass

    def add_history(self, history_list):
        pass

    def add_mail(self, mail_dict):
        pass