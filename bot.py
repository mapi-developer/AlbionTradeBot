from managers.market import MarketManager
from core.capture import WindowCapture
from net.sniffer import AlbionSniffer
from database.interface import DatabaseInterface
from managers.config import ConfigManager, PRESETS_DIR, ITEMS_BLACK_MARKET
import os
import re
import json
import threading
import time
from datetime import datetime, timezone

class TradeBot:
    db: DatabaseInterface

    def __init__(self, capture: WindowCapture = None, sniffer: AlbionSniffer = None, market_manager: MarketManager = None, db: DatabaseInterface = None):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.config_manager = ConfigManager()
        
        self.paused = False # Pause state flag

        if capture == None:
            capture = WindowCapture(base_dir=BASE_DIR, window_name="Albion Online Client")
        self.capture = capture

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

    def toggle_pause(self):
        """Toggles the pause state of the bot."""
        self.paused = not self.paused
        state = "PAUSED" if self.paused else "RESUMED"
        print(f"Bot state: {state}")
        return self.paused

    def _wait_if_paused(self):
        """Blocks execution if the bot is paused."""
        while self.paused:
            time.sleep(0.5)

    def load_preset_items(self, setting_key):
        """Loads items list from the preset file defined in settings."""
        preset_file = self.config_manager.get("city_presets")[setting_key]
        if not preset_file:
            print(f"[Error] No preset selected for '{setting_key}' in configuration.")
            return []
        
        path = os.path.join(PRESETS_DIR, preset_file)
        if not os.path.exists(path):
            print(f"[Error] Preset file not found: {path}")
            return []
            
        try:
            with open(path, "r") as f:
                return json.load(f) 
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
            items_to_check = list(ITEMS_BLACK_MARKET.values())
            print(f"Starting Black Market Price Check for {len(items_to_check)} items from dictionary...")
        else:
            items_to_check = self.load_preset_items(self.market_manager.get_market_title())
            if not items_to_check:
                print("No items to check. Please select a preset in Configuration.")
                return
            print(f"Starting Price Check for {len(items_to_check)} items...")

        self.market_manager.change_tab("buy")

        try:
            for item in items_to_check:
                self._wait_if_paused() # Check pause
                
                self.sniffer.clear_buffer()
                
                if isBlackMarket:
                    self.market_manager.search_item(item, black_market=True)
                else:
                    self.market_manager.search_item(item, from_db=True, black_market=False)
                    
                self.market_manager.sleep(.3)
                self.market_manager.check_pages()

                current_market_orders = self.sniffer.market_data_buffer
                if not current_market_orders:
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

    def remove_orders(self):
        while self.market_manager.order_exists():
            self._wait_if_paused() # Check pause
            self.market_manager.remove_order(25)
            self.market_manager.scroll()

    def buy_items(self, fast_buy: bool = False):
        self.capture.set_foreground_window()
        self.market_manager.change_tab("my_orders_tab")
        if self.market_manager.order_exists():
            self.remove_orders()
        items_to_buy_list = self.load_preset_items(self.market_manager.get_market_title())
        items_prices = self.db.get_all_prices_for_city("black_market")
        if self.config_manager.get("general")["buy_mode"] == "fast":
            fast_buy = True

        if not items_to_buy_list:
            print("No items to buy. Please select a preset in Configuration.")
            return

        print(f"Starting Buy Routine for {len(items_to_buy_list)} items...")
        self.market_manager.prepare()
            
        try:
            for item_unique_name in items_to_buy_list:
                self._wait_if_paused() # Check pause
                
                self.market_manager.search_item(item_unique_name, from_db=True)
                self.sniffer.clear_buffer()
                self.market_manager.open_item()
                self.market_manager.sleep(.3)

                current_market_orders = self.sniffer.market_data_buffer
                if not current_market_orders:
                    print(f"No data: {item_unique_name}")

                lowest_price = float('inf')
                order_price = 0
                
                for order in current_market_orders:
                    if order.get('AuctionType') == 'offer':
                        price = order.get('UnitPriceSilver', 0) / 10000
                        
                        if price < lowest_price and price > 0:
                            lowest_price = price
                
                for order in current_market_orders:
                    if order.get('AuctionType') == 'request':
                        price = order.get('UnitPriceSilver', 0) / 10000

                        if price > order_price and price > 0:
                            order_price = price
                min_profit_rate = self.config_manager.get("general")["min_profit_rate_order"] or 0.0

                if fast_buy == False:
                    lowest_price = order_price
                if fast_buy == True:
                    min_profit_rate = self.config_manager.get("general")["min_profit_rate_fast"] or 0.0

                black_market_price = 0
                try:
                    black_market_price = items_prices[item_unique_name] / 10000
                except:
                    self.market_manager.close_item()
                    continue

                potential_sell_price = black_market_price * 0.96 
                profit = potential_sell_price - lowest_price
                profit_margin = (profit / lowest_price) if lowest_price > 0 else 0

                if profit_margin >= min_profit_rate:
                    buy_logic_rules = self.config_manager.get("buy_logic") or []
                    sorted_rules = sorted(buy_logic_rules, key=lambda x: int(x.get('price', 0)), reverse=True)
                    
                    quantity_to_buy = 0
                    
                    for rule in sorted_rules:
                        price_threshold = int(rule['price_larger_then'])
                        if int(lowest_price) > price_threshold:
                            quantity_to_buy = int(rule['amount_to_buy'])
                    
                    if quantity_to_buy == 0:
                        quantity_to_buy = int(self.config_manager.get("general")["default_buy_amount"])

                    if quantity_to_buy > 0:
                        print(f"Profitable trade for {item_unique_name}! Price: {lowest_price}, Margin: {profit_margin*100:.2f}%. Buying {quantity_to_buy} units.")
                        self.market_manager.buy_item(amount=quantity_to_buy, fast_buy=fast_buy, fast_buy_price=int(lowest_price*1.05))
                    else:
                        print(f"Item {item_unique_name} is profitable, but its price ({lowest_price}) is above all configured buying thresholds. Skipping.")
                        self.market_manager.close_item()
                else:
                    print(f"Item {item_unique_name} not profitable enough. Margin: {profit_margin*100:.2f}%, Required: {min_profit_rate*100}%. Skipping.")
                    self.market_manager.close_item()
        except KeyboardInterrupt:
            print("Stopping bot...")

if __name__ == "__main__":
    bot = TradeBot()
    print(bot.market_manager.get_market_title())