import re
import threading
from .managers import SettingsManager, MarketManager, TravelManager, LoginManager ,Logger
from .core import WindowCapture
from .api import DatabaseInterface
from .net import AlbionSniffer
import gc
import os
import json
import time
import win32gui, win32api, win32con

def change_keyboard_layout(language_id_hex = 0x04090409):
    hwnd = win32gui.GetForegroundWindow()
    
    if hwnd:
        win32api.PostMessage(
            hwnd,
            win32con.WM_INPUTLANGCHANGEREQUEST,
            0,
            language_id_hex
        )
        print(f"Request sent to switch layout to: {hex(language_id_hex)}")
    else:
        print("No active window found.")


class Bot:
    def __init__(
            self, 
            capture: WindowCapture = None, 
            market_manager: MarketManager = None,
            travel_manager: TravelManager = None,
            login_manager: LoginManager = None,
            logger: Logger = None,
            sniffer: AlbionSniffer = None,
            overlay = None
        ):
        self.settings = SettingsManager()
        self.status = "Initializing"
        self.paused = False
        self.db = DatabaseInterface()
        if capture == None: capture = WindowCapture("Albion Online Client")
        if market_manager == None: market_manager = MarketManager(capture=capture, settings=self.settings)
        if travel_manager == None: travel_manager = TravelManager(self, capture=capture, settings=self.settings)
        if login_manager == None: login_manager = LoginManager(bot=self, capture=capture, settings=self.settings)
        if logger == None: logger = Logger()
        if sniffer == None: sniffer = AlbionSniffer()
        self.capture = capture
        self.market_manager = market_manager
        self.travel_manager = travel_manager
        self.login_manager = login_manager
        self.logger = logger
        self.sniffer = sniffer
        self.sniffer_thread = threading.Thread(target=self.sniffer.start, daemon=True)
        self.sniffer_thread.start()
        self.status = "Ready"
        self.current_task_name = "Ready"
        self.current_item_name = ""
        self.current_location = "island"
        self.sequence_settings = None
        self.min_silver = 0
        self.overlay = overlay
        self.recent_items = []

        self.logger.add_log("bot", f"Bot initialized!")

    def destroy(self):
        print("Destroying Bot instance...")
        self.status = "Destroying"

        if self.sniffer:
            self.sniffer.stop()

        if self.sniffer_thread and self.sniffer_thread.is_alive():
            self.sniffer_thread.join(timeout=1.0)
            if self.sniffer_thread.is_alive():
                print("Warning: Sniffer thread did not shut down cleanly.")
                self.logger.add_log("bot", f"Warning: Sniffer thread did not shut down cleanly.")

        if self.market_manager != None:
            self.market_manager.destroy()
            self.market_manager = None

        if self.db:
            if hasattr(self.db, 'close'):
                self.db.close()
            elif hasattr(self.db, 'disconnect'):
                self.db.disconnect()

        if self.capture and hasattr(self.capture, 'release'):
            self.capture.release()

        self.sniffer = None
        self.market_manager = None
        self.capture = None
        self.db = None
        self.settings = None
        
        gc.collect()
        print("Bot instance destroyed.")
        self.logger.add_log("app", f"Bot destroyed!")

    def load_preset_items(self, city: str):
        buy_mode = self.settings.get("general")["buy_mode"]
        preset_file = self.settings.get(buy_mode+"_buy")["presets"][city]
        if not preset_file:
            print(f"[Error] No preset selected for '{city}'")
            self.logger.add_log("error", f"[Error] No preset selected for '{city}'")
            return []
        
        path = os.path.join(self.settings.PRESETS_DIR, preset_file)
        if not os.path.exists(path):
            print(f"[Error] Preset file not found: {path}")
            self.logger.add_log("error", f"[Error] Preset file not found: {path}")
            return []
        
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Failed to load preset {preset_file}: {e}")
            self.logger.add_log("error", f"[Error] Failed to load preset {preset_file}: {e}")
            return []

    def toggle_pause(self):
        self.paused = not self.paused
        self.status = "Paused" if self.paused else "Running"
        self.logger.add_log("bot", f"Pause toggled status: {self.status}")
        if self.status == "Running":
            self.settings.settings = self.settings.load_settings()
            buy_mode = self.settings.get("general")["buy_mode"]
            self.sequence_settings = self.settings.get(f"{buy_mode}_buy")
            self.min_silver = self.settings.get("general")["min_silver"]
            change_keyboard_layout()

        return self.paused
    
    def _wait_if_paused(self):
        while self.paused:
            time.sleep(.5)
        self.capture.set_foreground_window()

    def parse_item_info(self, full_unique_name: str):
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

    def update_overlay(self):
        if self.overlay:
            self.overlay.send_update(
                status=self.status,
                task=self.current_task_name,
                paused=self.paused,
                recent_items=self.recent_items
            )

    def add_recent_item(self, name, price, type="check"):
        self.recent_items.insert(0, {"name": name, "price": str(price), "type": type})
        if len(self.recent_items) > 5:
            self.recent_items.pop()
        self.update_overlay()

    def check_price(self):
        self.recent_items = []
        self.status = "Running"
        self.capture.set_foreground_window()
        self.logger.add_log("bot", f"Bot Starting price checking for {self.current_location}")
        market_title = self.market_manager.get_market_title()
        self.current_location = market_title
        is_black_market = market_title == "black_market"

        if is_black_market:
            items_to_check = list(self.settings.ITEMS_BLACK_MARKET.values())
            print(f"Starting Black Market Price Check for {len(items_to_check)} items from dictionary...")
        else:
            items_to_check = self.load_preset_items(market_title)
            if not items_to_check:
                print("[Warning] No items to check. Please select a preset in Settings")
                return
            print(f"Starting Price Check for {len(items_to_check)} items in {market_title}")
        
        self.current_task_name = f"Cheking Price: 0/{len(items_to_check)}"
        self.market_manager.change_tab("buy")
        self.update_overlay()

        try:
            change_keyboard_layout()
            for i, item in enumerate(items_to_check):
                self._wait_if_paused()
                self.current_item_name = f"Scanning: {item}"

                if not self.paused:
                    self.current_task_name = f"Cheking Price: {i+1}/{len(items_to_check)}"
                    self.update_overlay()

                if is_black_market:
                    self.market_manager.search_item(item, black_market=True)
                else:
                    self.market_manager.search_item(item, from_db=True)

                self.market_manager.sleep(.3)
                self.market_manager.check_pages()

                current_market_orders = self.sniffer.get_market_buffer(type="request")
                if not current_market_orders:
                    print(f"No market data captured for: {item}")
                    self.logger.add_log("market", f"No market data captured for: {item} (price_check)")
                    self.add_recent_item(item, "N/A", "check")

                found_prices = {}
                for order in current_market_orders:
                    quality = order.get("QualityLevel", 1)
                    if quality > 3: continue

                    full_name = order.get("ItemTypeId", "Unknown")
                    base_name, tier, enchant = self.parse_item_info(full_unique_name=full_name)
                    raw_price = order.get("UnitPriceSilver", 0)
                    key = (base_name, tier, enchant)
                    if key not in found_prices:
                        found_prices[key] = raw_price
                    else:
                        if raw_price > found_prices[key]:
                            found_prices[key] = raw_price

                if found_prices:
                    self.add_recent_item(item, f"updated!", "check")
                    payload = []
                    for (base, tier, enc), price in found_prices.items():
                        if enc > 0: unique_name = f"{tier}_{base}@{enc}"
                        else: unique_name = f"{tier}_{base}"

                        item_data = {
                            "unique_name": unique_name,
                            f"price_{market_title}": int(price)
                        }
                        payload.append(item_data)
                    
                    if payload:
                        self.db.update_item_prices(payload, item_type="fast")
        except KeyboardInterrupt:
            print("Stopping bot...")

        self.status = "Ready"

    def remove_orders(self):
        self.sniffer.request_market_buffer.clear()
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Removing Orders"
        self.current_location = self.market_manager.get_market_title()
        self.logger.add_log("bot", f"Bot Starting to remove orders for {self.current_location}")
        self.capture.set_foreground_window()
        self.market_manager.change_tab("my_orders_tab")
        change_keyboard_layout()
        self.market_manager.remove_order(5)
        while self.sniffer.get_market_buffer(type="request") != []:
            self._wait_if_paused()
            self.market_manager.remove_order(5)
            self.market_manager.scroll()

        self.status = "Ready"

    def buy_items(self):
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Buying Items"
        self.capture.set_foreground_window()
        buy_mode = self.settings.get("general")["buy_mode"]
        market_title = self.market_manager.get_market_title()
        self.current_location = market_title
        is_fast_buy = buy_mode == "fast"
        items_to_buy_list = self.load_preset_items(market_title)
        items_prices = self.db.get_all_prices_for_city("black_market")
        self.min_silver = self.settings.get("general")["min_silver"]

        if not items_to_buy_list:
            print("No items to buy. Please select a preset in Settings")
            self.logger.add_log("market", f"No itmes to buy. Please select a preset in Settings")
            return
    
        print(f"Starting Buying {len(items_to_buy_list)} items in {market_title}")
        self.logger.add_log("market", f"Starting Buying {len(items_to_buy_list)} items in {market_title}")
        self.market_manager.prepare()

        try:
            self.sequence_settings = self.settings.get(f"{buy_mode}_buy")
            change_keyboard_layout()
            for i, item_unique_name in enumerate(items_to_buy_list):
                self._wait_if_paused()
                self.sniffer.market_buffer.clear()
                self.market_manager.search_item(item_unique_name, from_db=True)
                self.market_manager.open_item()
                self.market_manager.sleep(.5)

                if not self.paused:
                    self.current_task_name = f"Buy Items: {i+1}/{len(items_to_buy_list)}"
                    self.update_overlay()

                current_market_orders_offer, current_market_orders_request = self.sniffer.get_market_buffer()
                if current_market_orders_offer == [] and current_market_orders_request == []:
                    print(f"No data for {item_unique_name}")
                    self.logger.add_log("orders", f"No data for {item_unique_name}")
                    if is_fast_buy:
                        continue
                
                lowest_price = float('inf')
                order_price = 1

                if current_market_orders_offer != []:
                    for order in current_market_orders_offer:
                        if order.get("AuctionType") == "offer":
                            price = order.get("UnitPriceSilver", 0) / 10000
                            if price < lowest_price and price > 0:
                                lowest_price = price

                if not is_fast_buy:
                    if current_market_orders_request != []:
                        for order in current_market_orders_request:
                            if order.get("AuctionType") == "request":
                                price = order.get("UnitPriceSilver", 0) / 10000
                                if price > order_price and price > 0:
                                    order_price = price

                    lowest_price = order_price
                min_profit_rate = float(self.sequence_settings["min_profit_rate"])/100 or 0.0
                
                black_market_price = 0
                if item_unique_name in items_prices.keys():
                    black_market_price = items_prices[item_unique_name] / 10000
                else:
                    print(f"No black market data for {item_unique_name}")
                    self.logger.add_log("orders", f"No black market data for {item_unique_name}")
                    self.market_manager.close_item()
                    continue

                profit = black_market_price * 0.96 - lowest_price
                profit_margin = (profit / lowest_price) if lowest_price > 0 else profit

                if profit_margin >= min_profit_rate:
                    buy_logic_rules = [i for i in self.sequence_settings.get("buy_logic", []) if i["amount_to_buy"] != "" and i["price_larger_then"] != ""]
                    rules_sorted = sorted(buy_logic_rules, key=lambda x: int(x.get("price_larger_then", 0)), reverse=False)

                    quantity_to_buy = int(self.sequence_settings.get("default_buy_amount", 0))

                    for rule in rules_sorted:
                        price_threshold = int(rule.get("price_larger_then"))
                        if int(lowest_price) > price_threshold:
                            quantity_to_buy = int(rule.get("amount_to_buy"))

                    if quantity_to_buy > 0:
                        print(f"Profitable trade for {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Buying {quantity_to_buy} units")
                        self.logger.add_log("orders", f"Profit on {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Buying {quantity_to_buy} units | SilverBalance: {self.sniffer.current_silver}")
                        self.market_manager.buy_item(amount=quantity_to_buy, fast_buy=is_fast_buy, fast_buy_price=int(lowest_price*1.05))
                        self.add_recent_item(self.market_manager.get_name_from_unique(item_unique_name), f"{int(lowest_price)} x{quantity_to_buy}", "buy")
                    else:
                        print(f"Item {item_unique_name} is profitable, but price {lowest_price} is above thresholds")
                        self.logger.add_log("orders", f"Item {item_unique_name} is profitable, but price {lowest_price} is above thresholds")
                        self.market_manager.close_item()
                else:
                    self.market_manager.close_item()

                if self.sniffer.current_silver != 0 and int(self.min_silver) >= self.sniffer.current_silver:
                    print("[Warning] Silver amount is less than minimum to continue")
                    self.logger.add_log("orders", "[Warning] Silver amount is less than minimum to continue")
                    break
        except Exception as e:
            print(f"[Error] Buy items issue: {e}")
            self.logger.add_log("error", f"[Error] Buy items issue: {e}")
        
        self.status = "Ready"

    def travel_to(self, destination: str):
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Traveling"
        self.logger.add_log("travel", f"Bot Starting traveling to {destination}")
        self.capture.set_foreground_window()
        change_keyboard_layout()
        self.travel_manager.travel_to(destination=destination)

    def check_login(self):
        self.login_manager.check_login()


if __name__ == "__main__":
    bot = Bot()
    bot.check_price()