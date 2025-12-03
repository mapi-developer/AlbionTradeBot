from managers.market import MarketManager
from core.capture import WindowCapture
from net.sniffer import AlbionSniffer
from database.interface import DatabaseInterface
from managers.config_manager import ConfigManager, PRESETS_DIR
from utils.helper import ITEMS_BLACK_MARKET
import os
import re
import json
import threading
from datetime import datetime, timezone

class TradeBot:
    def __init__(self, capture: WindowCapture = None, sniffer: AlbionSniffer = None, market_manager: MarketManager = None, db: DatabaseInterface = None):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.config_manager = ConfigManager()

        if capture == None:
            capture = WindowCapture(base_dir=BASE_DIR, window_name="Albion Online Client")
        self.capture = capture
        capture.set_foreground_window()

        if market_manager == None:
            market_manager = MarketManager(capture=capture)
        self.market_manager = market_manager

        if db == None:
            db = DatabaseInterface()
        self.db = db

        if sniffer == None:
            sniffer = AlbionSniffer()
        self.sniffer = sniffer
        self.sniffer_thread = threading.Thread(target=self.sniffer.start, daemon=True)
        self.sniffer_thread.start()   

    def load_preset_items(self, setting_key):
        """Loads items list from the preset file defined in settings."""
        preset_file = self.config_manager.get(setting_key)
        if not preset_file:
            print(f"[Error] No preset selected for '{setting_key}' in configuration.")
            return []
        
        path = os.path.join(PRESETS_DIR, preset_file)
        if not os.path.exists(path):
            print(f"[Error] Preset file not found: {path}")
            return []
            
        try:
            with open(path, "r") as f:
                return json.load(f) # Should be a list of UniqueNames
        except Exception as e:
            print(f"Error loading preset {preset_file}: {e}")
            return []

    def parse_item_info(self, full_unique_name):
        if "@" in full_unique_name:
            parts = full_unique_name.split("@")
            base_with_tier = parts[0]
            try: enchant = int(parts[1])
            except: enchant = 0
        else:
            base_with_tier = full_unique_name
            enchant = 0

        match = re.match(r"(T\d+)_(.+)", base_with_tier)
        if match:
            tier = match.group(1)
            base_name = match.group(2)
        else:
            tier = "TX"
            base_name = base_with_tier

        return base_name, tier, enchant

    def check_price(self, isBlackMarket=True):
        self.capture.set_foreground_window()
        if isBlackMarket:
            # Use names from the Black Market dictionary values
            items_to_check = list(ITEMS_BLACK_MARKET.values())
            print(f"Starting Black Market Price Check for {len(items_to_check)} items from dictionary...")
        else:
            # Load items from the configured preset
            items_to_check = self.load_preset_items("check_price_preset")
            if not items_to_check:
                print("No items to check. Please select a preset in Configuration.")
                return
            print(f"Starting Price Check for {len(items_to_check)} items...")

        self.market_manager.change_tab("buy")

        try:
            for item in items_to_check:
                self.sniffer.clear_buffer()
                
                if isBlackMarket:
                    # Search using the name directly (item is the value from dictionary)
                    self.market_manager.search_item(item)
                else:
                    # Search using the unique name (item is the key/id from preset)
                    self.market_manager.search_item(item, from_db=True)
                    
                self.market_manager.sleep(.3)
                self.market_manager.check_pages()

                current_market_orders = self.sniffer.market_data_buffer
                if not current_market_orders:
                    # Use item as the identifier in the log
                    print(f"No market data captured for: {item}")

                found_prices = {}
                
                for order in current_market_orders:
                    quality = order.get('QualityLevel', 1)
                    if quality > 3: continue

                    full_name = order.get('ItemTypeId', 'Unknown')
                    base_name, tier, enchant = self.parse_item_info(full_name)
                    raw_price = order.get('UnitPriceSilver', 0)
                    real_price = order.get('unit_price_real', raw_price)

                    key = (base_name, tier, enchant)
                    if key not in found_prices: 
                        found_prices[key] = real_price
                    else:
                        if real_price > found_prices[key]:
                            found_prices[key] = real_price

                if found_prices:
                    db_payload = []
                    for (base, tier, enc), price in found_prices.items():
                        if enc > 0: unique_name = f"{tier}_{base}@{enc}"
                        else: unique_name = f"{tier}_{base}"

                        item_data = {
                            'unique_name': unique_name,
                            'price_black_market': int(price),
                            'black_market_updated_at': datetime.now(timezone.utc)
                        }
                        db_payload.append(item_data)

                    if db_payload:
                        self.db.update_item_prices(db_payload)
        except KeyboardInterrupt:
            print("Stopping bot...")

    def buy_items(self):
        self.capture.set_foreground_window()
        items_to_buy_list = self.load_preset_items("buy_items_preset_"+self.market_manager.get_market_title())
        if not items_to_buy_list:
            print("No items to buy. Please select a preset in Configuration.")
            return

        print(f"Starting Buy Routine for {len(items_to_buy_list)} items...")
        self.market_manager.change_tab("create_buy_order")
            
        try:
            for item_unique_name in items_to_buy_list:
                # Logic assumes item_unique_name is the base T-level item? 
                # Adjust if your preset contains full names like T4_BAG
                # If preset has "BAG", use "T8_"+... logic. 
                # Assuming preset has FULL Unique Names now:
                
                self.market_manager.search_item(item_unique_name, from_db=True)
                self.sniffer.clear_buffer()
                self.market_manager.open_item()
                self.market_manager.sleep(.3)

                current_market_orders = self.sniffer.market_data_buffer
                if not current_market_orders:
                    print(f"No data: {item_unique_name}")

                lowest_price = float('inf')
                best_quality = 0
                
                for order in current_market_orders:
                    if order.get('AuctionType') == 'offer':
                        price = order.get('UnitPriceSilver', 0) / 10000
                        quality = order.get('QualityLevel', 0)
                        
                        if price < lowest_price and price > 0:
                            lowest_price = price
                            best_quality = quality

                print(f"Lowest Price for {item_unique_name}: {lowest_price}")

                self.market_manager.close_item()
        except KeyboardInterrupt:
            print("Stopping bot...")

if __name__ == "__main__":
    bot = TradeBot()
    print(bot.market_manager.get_market_title())