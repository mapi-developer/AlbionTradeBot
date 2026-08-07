import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timezone

from .client import APIClient 

class DatabaseInterface:
    def __init__(self, db_path: str = "config/market_data.db"):
        self.db_path = db_path
        self.client = APIClient(db_path=self.db_path)
        print(f"✅ Interface initialized with Local DB: {self.db_path}")

    def check_connection_status(self) -> bool:
        """
        Pings the local SQLite database to ensure it is accessible.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                print("✅ Local Database connection is successful.")
                return True
        except Exception as e:
            print(f"❌ Local Database connection failed. Error: {e}")
            return False

    def update_item_prices(self, price_data_list: List[Dict], item_type: str = "fast", server: str = "US"):
        """
        Queue item price updates to the local database.
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
        Retrieves all item prices for a specific city directly from the local SQLite DB.
        """
        try:
            # Clean up the city name to match how it's stored in the DB (without 'price_' prefix)
            db_city = city.lower().replace(' ', '_')
            if db_city.startswith("price_"):
                db_city = db_city.replace("price_", "")
                
            result = {}
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Query the local database instead of making a GET request
                cursor.execute('''
                    SELECT unique_name, price 
                    FROM market_prices 
                    WHERE server = ? AND item_type = ? AND city = ?
                ''', (server, item_type, db_city))
                
                rows = cursor.fetchall()
                for unique_name, price in rows:
                    result[unique_name] = price
            
            return result

        except Exception as e:
            print(f"Exception fetching prices from local DB: {e}")
            return {}

    def get_last_update_at(self) -> Optional[datetime]:
        """
        Returns current local timestamp.
        """
        try:
            return datetime.now(timezone.utc) 
        except Exception:
            return None