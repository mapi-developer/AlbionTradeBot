import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

from .client import APIClient 


class DatabaseInterface:
    def __init__(self):
        load_dotenv()
        self.api_url = os.getenv('API_URL', "https://trade-backend-service-1014783260724.europe-west1.run.app")
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

    def update_item_prices(self, price_data_list: List[Dict], item_type: str = "fast", server: str = "US"):
        """
        Queue item price updates.
        :param item_type: 'fast' or 'order' 
        :param server: 'US', 'EU', or 'AS'
        """
        for entry in price_data_list:
            data = entry.copy()
            unique_name = data.pop('unique_name', None)
            
            if not unique_name:
                continue

            for key, price in data.items():
                if key.startswith('price_') and isinstance(price, (int, float)):
                    self.client.update_item_price(unique_name, key, int(price), item_type=item_type, server=server)

    def force_price_update(self):
        self.client.force_update()

    def get_all_prices_for_city(self, city: str, item_type: str = "fast", server: str = "US") -> Dict[str, int]:
        """
        Retrieves all item prices for a specific city via API.
        This fetches the full list for the server to avoid URL length limits (422 Errors).
        """
        try:
            # FIXED: Request all items for the server/type. Do NOT send item_names list.
            response = requests.get(
                f"{self.api_url}/items/", 
                params={"type": item_type, "server": server},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"API Error fetching prices: {response.status_code}")
                return {}

            items = response.json()
            city_key = f"price_{city.lower().replace(' ', '_')}"
            
            # Filter locally
            result = {}
            for item in items:
                price = item.get(city_key)
                if price:
                    result[item['unique_name']] = price
            
            return result

        except Exception as e:
            print(f"Exception fetching prices: {e}")
            return {}

    def get_last_update_at(self) -> Optional[datetime]:
        """
        Fetches the latest timestamp from the DB. 
        """
        try:
            return datetime.now(timezone.utc) 
        except Exception:
            return None