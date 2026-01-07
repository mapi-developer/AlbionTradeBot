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

    def update_item_prices(self, price_data_list: List[Dict], item_type: str = "fast"):
        """
        Queue item price updates.
        :param item_type: 'fast' or 'order' (default: 'fast')
        """
        for entry in price_data_list:
            # We copy to avoid modifying the original dict inside the loop
            data = entry.copy()
            unique_name = data.pop('unique_name', None)
            
            if not unique_name:
                continue

            # Iterate over keys to find prices (e.g., 'price_caerleon', 'price_martlock')
            for key, price in data.items():
                if key.startswith('price_') and isinstance(price, (int, float)):
                    # Queue the update using the client, passing the item_type
                    self.client.update_item_price(unique_name, key, int(price), item_type=item_type)

    def force_price_update(self):
        self.client.force_update()

    def get_all_prices_for_city(self, city: str, item_type: str = "fast") -> Dict[str, int]:
        """
        Retrieves all item prices for a specific city via API.
        :param item_type: 'fast' or 'order' to select which table to fetch from.
        """
        try:
            # Pass the type param to the backend
            response = requests.get(
                f"{self.api_url}/items/", 
                params={"type": item_type},
                timeout=10
            )
            
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
        """
        try:
            # Placeholder: In production, you might want a specific lightweight endpoint
            return datetime.utcnow() 
        except Exception:
            return None
