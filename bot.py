from managers.market import MarketManager
from core.capture import WindowCapture
from net.sniffer import AlbionSniffer
from database.interface import DatabaseInterface
import os
import re
import threading
from datetime import datetime, timezone
from config import ITEMS_TO_BUY, ITEMS_BLACK_MARKET

class TradeBot:
    def __init__(self, capture: WindowCapture = None, sniffer: AlbionSniffer = None, market_manager: MarketManager = None, db: DatabaseInterface = None):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

    def parse_item_info(self, full_unique_name):
        """
        Parses a full unique name into (BaseName, Tier, Enchantment).
        
        Example: 
        "T4_HEAD_CLOTH_ROYAL@1" -> ("HEAD_CLOTH_ROYAL", "T4", 1)
        "T5_MAIN_SWORD"         -> ("MAIN_SWORD", "T5", 0)
        """
        # 1. Extract Enchantment
        if "@" in full_unique_name:
            parts = full_unique_name.split("@")
            base_with_tier = parts[0]
            try:
                enchant = int(parts[1])
            except:
                enchant = 0
        else:
            base_with_tier = full_unique_name
            enchant = 0

        # 2. Extract Tier and Base Name
        # Regex looks for T{number}_ at the start
        match = re.match(r"(T\d+)_(.+)", base_with_tier)
        if match:
            tier = match.group(1)   # e.g. "T4"
            base_name = match.group(2) # e.g. "HEAD_CLOTH_ROYAL"
        else:
            tier = "TX"
            base_name = base_with_tier

        return base_name, tier, enchant

    def check_price(self):
        self.market_manager.change_tab("buy")

        try:
            for item_unique_name in ITEMS_BLACK_MARKET:
                self.sniffer.clear_buffer()
                self.market_manager.search_item(ITEMS_BLACK_MARKET[item_unique_name], from_db=True)
                self.market_manager.sleep(.5)

                self.market_manager.check_pages()

                current_market_orders = self.sniffer.market_data_buffer

                if not current_market_orders:
                    print(f"No market data captured for item: {item_unique_name}")

                found_prices = {}
                
                for order in current_market_orders:
                    # --- A. Quality Check ---
                    # QualityLevel: 1=Normal, 2=Good, 3=Outstanding, etc.
                    # User requirement: Only quality < 3
                    quality = order.get('QualityLevel', 1)
                    if quality > 3:
                        continue

                    # --- B. Parse Item Info ---
                    full_name = order.get('ItemTypeId', 'Unknown')
                    base_name, tier, enchant = self.parse_item_info(full_name)

                    # --- C. Price Conversion ---
                    raw_price = order.get('UnitPriceSilver', 0)
                    # Check if sniffer already converted it, otherwise divide by 10000
                    real_price = order.get('unit_price_real', raw_price)

                    # --- D. Store Highest Price ---
                    # Key includes Base Name to handle different items safely
                    key = (base_name, tier, enchant)

                    if key not in found_prices: 
                        found_prices[key] = real_price
                    else:
                        # We want the HIGHEST price (standard for Black Market flipping)
                        if real_price > found_prices[key]:
                            found_prices[key] = real_price

                # 5. Print Results for this search
                if not found_prices:
                    print("   No valid orders found (Quality < 4).")
                else:
                    if found_prices:
                        db_payload = []
                        
                        for (base, tier, enc), price in found_prices.items():
                            # Reconstruct UniqueName (e.g. T4_BAG or T4_BAG@1)
                            if enc > 0:
                                unique_name = f"{tier}_{base}@{enc}"
                            else:
                                unique_name = f"{tier}_{base}"

                            # Create DB Entry
                            # Mapping Black Market Price -> price_caerleon
                            item_data = {
                                'unique_name': unique_name,
                                'price_black_market': int(price),
                                'black_market_updated_at': datetime.now(timezone.utc)
                            }
                            db_payload.append(item_data)

                        # C. Update Database
                        if db_payload:
                            self.db.update_item_prices(db_payload)
                            #print(f"   [DB] Sent updates for {len(db_payload)} items.")
                            self.market_manager.sleep(0.5)
        except KeyboardInterrupt:
            print("Stopping bot...")

    def buy_items(self):
        self.market_manager.change_tab("buy")
            
        try:
            for item_unique_name in ITEMS_TO_BUY:
                self.market_manager.search_item("T8_"+item_unique_name, from_db=True)
                self.sniffer.clear_buffer()
                self.market_manager.open_item()

                self.market_manager.sleep(.5)

                current_market_orders = self.sniffer.market_data_buffer

                if not current_market_orders:
                    print(f"No market data captured for item: {"T8_"+item_unique_name}")

                lowest_price = float('inf')
                best_quality = 0
                
                for order in current_market_orders:
                    if order.get('AuctionType') == 'offer':
                        price = order.get('UnitPriceSilver', 0) / 10000
                        quality = order.get('QualityLevel', 0)
                        
                        if price < lowest_price and price > 0:
                            lowest_price = price
                            best_quality = quality

                #print(f"Captured {len(current_market_orders)} orders.")
                print(f"Lowest Price found: {lowest_price} (Quality: {best_quality})")
                self.market_manager.close_item()
        except KeyboardInterrupt:
            print("Stopping bot...")

if __name__ == "__main__":
    bot = TradeBot()
    bot.check_price()