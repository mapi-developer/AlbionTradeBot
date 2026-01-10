import re
import threading
from .managers import (
    SettingsManager,
    MarketManager,
    TravelManager,
    LoginManager,
    Logger,
    ChestManager
)
from .core import WindowCapture
from .api import DatabaseInterface
from .net import AlbionSniffer
import gc
import os
import json
import time
import win32gui, win32api, win32con

GLOBAL_SNIFFER = None
GLOBAL_SNIFFER_THREAD = None


def change_keyboard_layout(language_id_hex=0x04090409):
    hwnd = win32gui.GetForegroundWindow()

    if hwnd:
        win32api.PostMessage(
            hwnd, win32con.WM_INPUTLANGCHANGEREQUEST, 0, language_id_hex
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
        chest_manager: ChestManager = None,
        logger: Logger = None,
        sniffer: AlbionSniffer = None,
        overlay=None,
    ):

        global GLOBAL_SNIFFER, GLOBAL_SNIFFER_THREAD

        # Logic: If a global sniffer exists, use it. If not, create it ONCE.
        if sniffer is None:
            if GLOBAL_SNIFFER is None:
                print("Initializing Global Sniffer...")
                GLOBAL_SNIFFER = AlbionSniffer()
                GLOBAL_SNIFFER_THREAD = threading.Thread(
                    target=GLOBAL_SNIFFER.start, daemon=True
                )
                GLOBAL_SNIFFER_THREAD.start()

            self.sniffer = GLOBAL_SNIFFER

        self.settings = SettingsManager()
        self.status = "Initializing"
        self.paused = False
        self.db = DatabaseInterface()
        if capture == None:
            capture = WindowCapture("Albion Online Client")
        if market_manager == None:
            market_manager = MarketManager(capture=capture, settings=self.settings)
        if travel_manager == None:
            travel_manager = TravelManager(
                self, capture=capture, settings=self.settings
            )
        if login_manager == None:
            login_manager = LoginManager(
                bot=self, capture=capture, settings=self.settings
            )
        if chest_manager == None: chest_manager = ChestManager(capture=capture, settings=self.settings)
        if logger == None:
            logger = Logger()
        self.capture = capture
        self.market_manager = market_manager
        self.travel_manager = travel_manager
        self.login_manager = login_manager
        self.chest_manager = chest_manager
        self.logger = logger
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

        if self.market_manager != None:
            self.market_manager.destroy()
            self.market_manager = None

        if self.db:
            if hasattr(self.db, "close"):
                self.db.close()
            elif hasattr(self.db, "disconnect"):
                self.db.disconnect()

        if self.capture and hasattr(self.capture, "release"):
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
        preset_file = self.settings.get(buy_mode + "_buy")["presets"][city]
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
            self.logger.add_log(
                "error", f"[Error] Failed to load preset {preset_file}: {e}"
            )
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
            time.sleep(0.5)
        self.capture.set_foreground_window()

    def parse_item_info(self, full_unique_name: str):
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
                recent_items=self.recent_items,
            )

    def add_recent_item(self, name, price, type="check"):
        self.recent_items.insert(0, {"name": name, "price": str(price), "type": type})
        if len(self.recent_items) > 5:
            self.recent_items.pop()
        self.update_overlay()

    def _calculate_price_extremum(self, orders, find_min=True):
        """
        Calculates minimal or maximal price from a list of orders.
        Returns a dictionary {(base, tier, enchant): price}
        """
        found_prices = {}
        for order in orders:
            quality = order.get("QualityLevel", 1)
            if quality > 3:
                continue

            full_name = order.get("ItemTypeId", "Unknown")
            base_name, tier, enchant = self.parse_item_info(full_unique_name=full_name)
            raw_price = order.get("UnitPriceSilver", 0)
            key = (base_name, tier, enchant)

            if key not in found_prices:
                found_prices[key] = raw_price
            else:
                if find_min:
                    if raw_price < found_prices[key]:
                        found_prices[key] = raw_price
                else:  # find max
                    if raw_price > found_prices[key]:
                        found_prices[key] = raw_price
        return found_prices

    def update_market_prices(self, market_title, offers=None, requests=None):
        """
        Updates database prices based on market buffers according to user rules.
        
        NEW RULE:
        - OFFERS (Sell Orders) -> Update into 'fast' datatable (using MIN price)
        - REQUESTS (Buy Orders) -> Update into 'order' datatable (using MAX price)
        
        Returns a tuple of dicts ({unique_name: price}, {unique_name: price}) for offers and requests.
        """
        updated_offers = {}
        updated_requests = {}

        # 1. Process Offers (Sell Orders) -> "fast" table (Min Price)
        if offers:
            found_offers = self._calculate_price_extremum(offers, find_min=True)
            if found_offers:
                payload = []
                for (base, tier, enc), price in found_offers.items():
                    unique_name = f"{tier}_{base}@{enc}" if enc > 0 else f"{tier}_{base}"
                    updated_offers[unique_name] = price
                    payload.append({
                        "unique_name": unique_name,
                        f"price_{market_title}": int(price),
                    })
                
                if payload:
                    # CHANGED: Offers now map to 'fast'
                    self.db.update_item_prices(payload, item_type="fast")

        # 2. Process Requests (Buy Orders) -> "order" table (Max Price)
        if requests:
            found_requests = self._calculate_price_extremum(requests, find_min=False)
            if found_requests:
                payload = []
                for (base, tier, enc), price in found_requests.items():
                    unique_name = f"{tier}_{base}@{enc}" if enc > 0 else f"{tier}_{base}"
                    updated_requests[unique_name] = price
                    payload.append({
                        "unique_name": unique_name,
                        f"price_{market_title}": int(price),
                    })

                if payload:
                    # CHANGED: Requests now map to 'order'
                    self.db.update_item_prices(payload, item_type="order")
        
        return updated_offers, updated_requests

    def check_price(self):
        self.recent_items = []
        self.status = "Running"
        self.capture.set_foreground_window()
        self.logger.add_log(
            "bot", f"Bot Starting price checking for {self.current_location}"
        )
        market_title = self.market_manager.get_market_title()
        self.current_location = market_title
        is_black_market = market_title == "black_market"

        if is_black_market:
            items_to_check = list(self.settings.ITEMS_BLACK_MARKET.values())
            print(
                f"Starting Black Market Price Check for {len(items_to_check)} items from dictionary..."
            )
        else:
            items_to_check = self.load_preset_items(market_title)
            if not items_to_check:
                print("[Warning] No items to check. Please select a preset in Settings")
                return
            print(
                f"Starting Price Check for {len(items_to_check)} items in {market_title}"
            )

        self.current_task_name = f"Cheking Price: 0/{len(items_to_check)}"
        self.market_manager.change_tab("buy")
        self.update_overlay()

        try:
            change_keyboard_layout()
            for i, item in enumerate(items_to_check):
                self._wait_if_paused()
                self.current_item_name = f"Scanning: {item}"

                if not self.paused:
                    self.current_task_name = (
                        f"Cheking Price: {i+1}/{len(items_to_check)}"
                    )
                    self.update_overlay()

                if is_black_market:
                    self.market_manager.search_item(item, black_market=True)
                else:
                    self.market_manager.search_item(item, from_db=True)

                self.market_manager.sleep(0.3)
                self.market_manager.check_pages()

                # CHANGED: Retrieve both buffers to ensure we get the right data
                current_offers, current_requests = self.sniffer.get_market_buffer()
                
                if not current_offers and not current_requests:
                    print(f"No market data captured for: {item}")
                    self.logger.add_log(
                        "market", f"No market data captured for: {item} (price_check)"
                    )
                    self.add_recent_item(item, "N/A", "check")
                
                # CHANGED: Use update_market_prices with new rules
                # Offers -> Fast, Requests -> Order
                updated_offers, updated_requests = self.update_market_prices(
                    market_title, offers=current_offers, requests=current_requests
                )

                if updated_offers:
                    self.add_recent_item(item, f"fast updated!", "check")
                    self.logger.add_log("market", f"{item} fast price checked")
                
                if updated_requests:
                    self.add_recent_item(item, f"order updated!", "check")
                    self.logger.add_log("market", f"{item} order price checked")

            self.db.force_price_update()
        except KeyboardInterrupt:
            print("Stopping bot...")

        self.status = "Ready"

    def check_bm_from_inventory(self):
        try:
            for x in range(6):
                self.overlay.stop()
                self.travel_manager.from_island_to_chest()
                if x == 0:
                    self.chest_manager.take_mount()
                    self.chest_manager.sleep(.5)
                    self.chest_manager.take_items_from_tab()
                elif x == 5:
                    self.chest_manager.stash_item_into_tab()
                    self.chest_manager.sleep(.5)
                    self.chest_manager.stash_mount()
                    self.chest_manager.sleep(.5)
                    self.chest_manager.from_tab_to_tab()
                    continue
                else:
                    self.chest_manager.stash_item_into_tab()
                    self.chest_manager.sleep(.5)
                    self.chest_manager.take_items_from_tab()
                
                self.sniffer.clear_inventory()
                self.travel_manager.from_island_chest_to_black_market()
                self.overlay.start()
                self.market_manager.sleep(2)
                self.market_manager.change_tab("sell")
                market_title = self.market_manager.get_market_title()
                self.current_location = market_title
                self.logger.add_log(
                    "bot", f"Bot Starting order price checking for {self.current_location}"
                )
                inventory_items = list(self.sniffer.get_inventory().values())
                for i, item in enumerate(inventory_items):
                    self._wait_if_paused()
                    item_name = self.market_manager.get_name_from_index(str(item))
                    self.current_item_name = f"Scanning: {item_name}"

                    if not self.paused:
                        self.current_task_name = (
                            f"Cheking Price: {i+1}/{len(inventory_items)}"
                        )
                        self.update_overlay()

                    self.market_manager.search_item(item_name, black_market=True)
                    self.market_manager.open_item()
                    self.market_manager.sleep(0.3)
                    self.market_manager.check_all_item_orders(
                        minimal_item_tier=self.settings.SPECIAL_ITEMS_BM.get(str(item), 4)
                    )
                    self.market_manager.close_item()

                    current_offers, current_requests = self.sniffer.get_market_buffer()

                    if not current_offers and not current_requests:
                        print(f"No market data captured for: {item}")
                        self.logger.add_log(
                            "market", f"No market data captured for: {item} (price_check)"
                        )
                        self.add_recent_item(item, "N/A", "check")

                    # CHANGED: Use update_market_prices with new rules
                    updated_offers, updated_requests = self.update_market_prices(
                        market_title, offers=current_offers, requests=current_requests
                    )

                    if updated_offers:
                        self.add_recent_item(item, f"fast updated!", "check")
                        self.logger.add_log("market", f"{item_name} fast price checked")

                    if updated_requests:
                        self.add_recent_item(item, f"order updated!", "check")
                        self.logger.add_log("market", f"{item_name} order price checked")

                self.db.force_price_update()
                self.travel_to("Matvey4a Guild's Island - Caerleon")
            self.current_location = "guild_chest_caerleon"
        except Exception as e:
            self.logger.add_log("market", f"Order BM price cheking Error: {e}")

    def check_price_order(self):
        self.status = "Running"
        self.overlay.start()
        self.capture.set_foreground_window()
        self.current_task_name = f"Cheking Price: 0/X"
        self.check_login()
        change_keyboard_layout()
        try:
            market_title = self.market_manager.get_market_title()
            if market_title == None:
                self.check_bm_from_inventory()
                return
            else:
                self.current_location = market_title
            self.overlay.start()
            self.market_manager.sleep(.5)
            self.market_manager.change_tab("buy")
            self.logger.add_log(
                    "bot", f"Bot Starting order price checking for {self.current_location}"
                )
            items_to_check = list(self.settings.ITEMS_BLACK_MARKET.values())
            self.market_manager.prepare(True)
            for i, item in enumerate(items_to_check):
                self._wait_if_paused()
                item_name = item
                self.current_item_name = f"Scanning: {item_name}"

                if not self.paused:
                    self.current_task_name = (
                        f"Cheking Price: {i+1}/{len(items_to_check)}"
                    )
                    self.update_overlay()

                self.market_manager.search_item(item_name, black_market=True)
                self.market_manager.open_item()
                self.market_manager.sleep(0.3)
                self.market_manager.check_all_item_orders(
                    minimal_item_tier=self.settings.SPECIAL_ITEMS.get(str(item), 4)
                )
                self.market_manager.close_item()

                current_offers, current_requests = self.sniffer.get_market_buffer()

                if not current_offers and not current_requests:
                    print(f"No market data captured for: {item}")
                    self.logger.add_log(
                        "market", f"No market data captured for: {item} (price_check)"
                    )
                    self.add_recent_item(item, "N/A", "check")

                # CHANGED: Use update_market_prices with new rules
                updated_offers, updated_requests = self.update_market_prices(
                    market_title, offers=current_offers, requests=current_requests
                )

                if updated_offers:
                    self.add_recent_item(item, f"fast updated!", "check")
                    self.logger.add_log("market", f"{item_name} fast price checked")

                if updated_requests:
                    self.add_recent_item(item, f"order updated!", "check")
                    self.logger.add_log("market", f"{item_name} order price checked")

            self.db.force_price_update()
        except Exception as e:
            self.logger.add_log("market", f"Order price cheking Error: {e}")

    def update_orders(self):
        def filter_bought_items(orders_list, items_to_buy):
            existing_order_ids = {order.get('ItemTypeId') for order in orders_list}

            remaining_items = [item for item in items_to_buy if item not in existing_order_ids]

            return remaining_items

        try:
            self.status = "Running"
            self.capture.set_foreground_window()
            self.overlay.start()
            market_title = self.market_manager.get_market_title()
            self.current_task_name = "Orders Update"
            self.logger.add_log("market", f"Bot Starting to update existing orders for {market_title}")
            items_to_buy_list = self.load_preset_items(market_title)
            items_prices_order = self.db.get_all_prices_for_city("black_market", item_type="fast")
            items_prices_fast = self.db.get_all_prices_for_city("black_market", item_type="order")
            self.min_silver = self.settings.get("general")["min_silver"]
            self.sequence_settings = self.settings.get(f"order_buy")
            
            if not items_to_buy_list:
                print("No items to buy. Please select a preset in Settings")
                self.logger.add_log(
                    "market", f"No itmes to buy. Please select a preset in Settings"
                )
                return
            self.market_manager.prepare_for_order_update()
            self.sniffer.clear_market_buffer()
            self.market_manager.sleep(.3)
            self.market_manager.reset_my_orders()
            orders_exists = []
            temp_orders_exists = self.sniffer.get_market_buffer("request")
            while len(temp_orders_exists) != 0:
                orders_exists.extend(temp_orders_exists)
                self.market_manager.next_my_orders_page()
                self.market_manager.sleep(.3)
                temp_orders_exists = self.sniffer.get_market_buffer("request")
                self.market_manager.sleep(.2)
            self.market_manager.prepare_for_order_update()
            my_character = orders_exists[0].get("BuyerName")
            for i, exist_order in enumerate(orders_exists):
                item_unique_name = exist_order.get("ItemTypeId")
                self._wait_if_paused()
                self.sniffer.clear_market_buffer()
                if not self.paused:
                    self.current_task_name = (
                        f"Updating Orders: {i+1}/{len(orders_exists)}"
                    )
                    self.update_overlay()

                self.market_manager.search_item(item_unique_name, from_db=True, black_market=False)
                self.market_manager.open_item(isEditOrder=True)
                self.market_manager.sleep(0.5)

                black_market_price = 0
                black_market_price_fast = 0
                if item_unique_name in items_prices_fast.keys():
                    black_market_price_fast = items_prices_fast[item_unique_name] / 10000
                black_market_price_order = 0
                if item_unique_name in items_prices_order.keys():
                    black_market_price_order = items_prices_order[item_unique_name] / 10000

                if black_market_price_fast == 0 and black_market_price_order == 0:
                    print(f"No black market data for {item_unique_name}")
                    self.logger.add_log(
                        "orders", f"No black market data for {item_unique_name}"
                    )
                    self.market_manager.close_item()
                    continue
                else:
                    if black_market_price_order > black_market_price_fast:
                        black_market_price = black_market_price_order
                    else:
                        black_market_price = black_market_price_fast

                current_offer, current_requests = self.sniffer.get_market_buffer()
                self.update_market_prices(market_title, current_offer, current_requests)
                if len(current_requests) != 0:
                    lowest_price = float("inf")
                    order_price = 1
                    current_amount = 0
                    current_buyer = ""
                    if len(current_requests) != 0:
                        for order in current_requests:
                            if order.get("AuctionType") == "request" and order.get("ItemTypeId") == item_unique_name:
                                if order.get("BuyerName") == my_character:
                                    current_amount = int(order.get("Amount"))
                                price = order.get("UnitPriceSilver", 0) / 10000
                                if price > order_price and price > 0:
                                    order_price = price
                                    current_buyer = order.get("BuyerName", "")
                    
                    lowest_price = order_price
                    print(item_unique_name, lowest_price, current_buyer)
                    if current_buyer == my_character:
                        self.market_manager.close_item()
                        continue

                    profit = black_market_price * 0.96 - lowest_price
                    profit_margin = (profit / lowest_price) if lowest_price > 0 else profit
                    min_profit_rate = (
                        float(self.sequence_settings["min_profit_rate"]) / 100 or 0.0
                    )
                    if profit_margin >= min_profit_rate:
                        buy_logic_rules = [
                            i
                            for i in self.sequence_settings.get("buy_logic", [])
                            if i["amount_to_buy"] != "" and i["price_larger_then"] != ""
                        ]
                        rules_sorted = sorted(
                            buy_logic_rules,
                            key=lambda x: int(x.get("price_larger_then", 0)),
                            reverse=False,
                        )

                        quantity_to_buy = int(
                            self.sequence_settings.get("default_buy_amount", 0)
                        )

                        for rule in rules_sorted:
                            price_threshold = int(rule.get("price_larger_then"))
                            if int(lowest_price) > price_threshold:
                                quantity_to_buy = int(rule.get("amount_to_buy"))

                        if quantity_to_buy > 0:
                            print(
                                f"Profitable Order for {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Qty: {quantity_to_buy}"
                            )
                            self.logger.add_log(
                                "orders",
                                f"Placing Order {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Qty: {quantity_to_buy} | Silver: {self.sniffer.current_silver}",
                            )
                            # Create Buy Order (fast_buy=False means +1 silver logic usually, or explicit price)
                            print(quantity_to_buy, current_amount)
                            self.market_manager.buy_item(
                                amount=(quantity_to_buy-current_amount+1),
                                fast_buy=True,
                                fast_buy_price=int(lowest_price+1)
                            )
                            self.add_recent_item(
                                self.market_manager.get_name_from_unique(item_unique_name),
                                f"{int(lowest_price+1)} x{quantity_to_buy}",
                                "order",
                            )
                        else:
                            print(f"Item {item_unique_name} profitable but quantity filtered by logic.")
                            self.market_manager.close_item()
                    else:
                        self.market_manager.close_item()
                        self.market_manager.remove_order(1)

                    if (
                        self.sniffer.current_silver != 0
                        and int(self.min_silver) >= self.sniffer.current_silver
                    ):
                        print("[Warning] Silver amount is less than minimum to continue")
                        self.logger.add_log(
                            "orders",
                            "[Warning] Silver amount is less than minimum to continue",
                        )
                        break
            
            if (
                self.sniffer.current_silver != 0
                and int(self.min_silver) >= self.sniffer.current_silver
            ):
                print("[Warning] Silver amount is less than minimum to continue")
                self.logger.add_log(
                    "orders",
                    "[Warning] Silver amount is less than minimum to continue",
                )
                return

            final_buy_list = filter_bought_items(orders_exists, items_to_buy_list)
            
            self.buy_items(final_buy_list)
        except Exception as e:
            self.logger.add_log("market", f"Error while updating orders: {e}")
            print(e)

    def remove_orders(self): 
        self.sniffer.clear_market_buffer()
        requests = len(self.sniffer.get_market_buffer("request"))
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Removing Orders"
        self.current_location = self.market_manager.get_market_title()
        self.logger.add_log(
            "bot", f"Bot Starting to remove orders for {self.current_location}"
        )
        self.capture.set_foreground_window()
        self.market_manager.change_tab("my_orders_tab")
        change_keyboard_layout()
        self.market_manager.remove_order(5)
        self.market_manager.scroll()
        requests = len(self.sniffer.get_market_buffer("request"))
        while requests != 0:
            self._wait_if_paused()
            self.market_manager.remove_order(5)
            self.market_manager.scroll()
            requests = len(self.sniffer.get_market_buffer("request"))
        self.status = "Ready"

    def buy_items(self, items_to_buy_list: list = None):
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Buying Items"
        self.capture.set_foreground_window()
        buy_mode = self.settings.get("general")["buy_mode"]
        market_title = self.market_manager.get_market_title()
        self.current_location = market_title
        is_fast_buy = buy_mode == "fast"
        if items_to_buy_list == None:
            items_to_buy_list = self.load_preset_items(market_title)
        items_prices_order = self.db.get_all_prices_for_city("black_market", item_type="fast")
        items_prices_fast = self.db.get_all_prices_for_city("black_market", item_type="order")
        self.min_silver = self.settings.get("general")["min_silver"]

        if not items_to_buy_list:
            print("No items to buy. Please select a preset in Settings")
            self.logger.add_log(
                "market", f"No itmes to buy. Please select a preset in Settings"
            )
            return

        print(f"Starting Buying {len(items_to_buy_list)} items in {market_title}")
        self.logger.add_log(
            "market",
            f"Starting Buying {len(items_to_buy_list)} items in {market_title}",
        )
        self.market_manager.prepare()

        try:
            self.sequence_settings = self.settings.get(f"{buy_mode}_buy")
            change_keyboard_layout()
            for i, item_unique_name in enumerate(items_to_buy_list):
                self._wait_if_paused()
                if not self.paused:
                    self.current_task_name = (
                        f"Buy Items: {i+1}/{len(items_to_buy_list)}"
                    )
                    self.update_overlay()

                self.sniffer.clear_market_buffer()
                self.market_manager.search_item(item_unique_name, from_db=True, black_market=False)
                self.market_manager.open_item()
                self.market_manager.sleep(0.5)

                current_offers, current_requests = self.sniffer.get_market_buffer()
                
                # CHANGED: Auto-update prices while buying according to new rule
                self.update_market_prices(
                    market_title, offers=current_offers, requests=current_requests
                )

                # Basic data validation
                if (len(current_offers) == 0 and len(current_requests) == 0):
                    print(f"No data for {item_unique_name}")
                    self.logger.add_log("orders", f"No data for {item_unique_name}")
                    if is_fast_buy:
                        self.market_manager.close_item()
                        continue

                # Determine Black Market Price (Reading existing DB logic untouched)
                black_market_price = 0
                black_market_price_fast = 0
                if item_unique_name in items_prices_fast.keys():
                    black_market_price_fast = items_prices_fast[item_unique_name] / 10000
                black_market_price_order = 0
                if item_unique_name in items_prices_order.keys():
                    black_market_price_order = items_prices_order[item_unique_name] / 10000

                if black_market_price_fast == 0 and black_market_price_order == 0:
                    print(f"No black market data for {item_unique_name}")
                    self.logger.add_log(
                        "orders", f"No black market data for {item_unique_name}"
                    )
                    self.market_manager.close_item()
                    continue
                else:
                    if black_market_price_order > black_market_price_fast:
                        black_market_price = black_market_price_order
                    else:
                        black_market_price = black_market_price_fast

                min_profit_rate = (
                    float(self.sequence_settings["min_profit_rate"]) / 100 or 0.0
                )

                # --- FAST BUY LOGIC (Cumulative Average Strategy) ---
                if is_fast_buy:
                    if not current_offers:
                        self.market_manager.close_item()
                        continue

                    # Filter for sell offers and sort by price ascending
                    offers = [o for o in current_offers if o.get("AuctionType") == "offer"]
                    offers.sort(key=lambda x: x.get("UnitPriceSilver", 0))

                    cumulative_cost = 0
                    cumulative_qty = 0
                    final_buy_qty = 0
                    final_max_price = 0
                    final_avg_price = 0
                    final_profit_margin = 0

                    for order in offers:
                        price = order.get("UnitPriceSilver", 0) / 10000
                        amount = order.get("Amount", 0) 
                        
                        if price <= 0 or amount <= 0:
                            continue

                        # Check batch statistics if we include this order
                        temp_cost = cumulative_cost + (price * amount)
                        temp_qty = cumulative_qty + amount
                        avg_price = temp_cost / temp_qty

                        profit = black_market_price * 0.96 - avg_price
                        profit_margin = (profit / avg_price) if avg_price > 0 else 0

                        # If the batch (including this order) is still profitable, add it
                        if profit_margin >= min_profit_rate:
                            cumulative_cost = temp_cost
                            cumulative_qty = temp_qty
                            final_buy_qty = cumulative_qty
                            final_max_price = price
                            final_avg_price = avg_price
                            final_profit_margin = profit_margin
                        else:
                            # If adding this order drops us below profitability, stop here
                            break

                    buy_logic_rules = [
                        i
                        for i in self.sequence_settings.get("buy_logic", [])
                        if i["amount_to_buy"] != "" and i["price_larger_then"] != ""
                    ]
                    rules_sorted = sorted(
                        buy_logic_rules,
                        key=lambda x: int(x.get("price_larger_then", 0)),
                        reverse=False,
                    )

                    quantity_to_buy = int(
                        self.sequence_settings.get("default_buy_amount", 0)
                    )

                    for rule in rules_sorted:
                        price_threshold = int(rule.get("price_larger_then"))
                        if int(final_avg_price) > price_threshold:
                            quantity_to_buy = int(rule.get("amount_to_buy"))

                    final_buy_qty = min(final_buy_qty, quantity_to_buy)

                    if final_buy_qty > 0:
                        print(
                            f"Profitable batch for {item_unique_name} | Qty: {final_buy_qty} | Avg Price: {final_avg_price:.2f} | Max Price: {final_max_price} | Margin: {final_profit_margin*100:.2f}%"
                        )
                        self.logger.add_log(
                            "orders",
                            f"Buying Batch {item_unique_name} | Qty: {final_buy_qty} | Avg: {final_avg_price:.2f} | Max: {final_max_price} | Margin: {final_profit_margin*100:.2f}% | Silver: {self.sniffer.current_silver}",
                        )
                        
                        # Execute Fast Buy for the total quantity at the max price needed to clear them
                        self.market_manager.buy_item(
                            amount=final_buy_qty,
                            fast_buy=True,
                            fast_buy_price=int(final_max_price)
                        )
                        
                        self.add_recent_item(
                            self.market_manager.get_name_from_unique(item_unique_name),
                            f"~{int(final_avg_price)} x{final_buy_qty}",
                            "buy",
                        )
                    else:
                        print(f"No profitable batch found for {item_unique_name}")
                        self.market_manager.close_item()

                # --- ORDER LOGIC (Place Buy Order) ---
                else:
                    lowest_price = float("inf")
                    order_price = 1

                    if current_requests != []:
                        for order in current_requests:
                            if order.get("AuctionType") == "request":
                                price = order.get("UnitPriceSilver", 0) / 10000
                                if price > order_price and price > 0:
                                    order_price = price
                    
                    lowest_price = order_price

                    profit = black_market_price * 0.96 - lowest_price
                    profit_margin = (profit / lowest_price) if lowest_price > 0 else profit

                    if profit_margin >= min_profit_rate:
                        buy_logic_rules = [
                            i
                            for i in self.sequence_settings.get("buy_logic", [])
                            if i["amount_to_buy"] != "" and i["price_larger_then"] != ""
                        ]
                        rules_sorted = sorted(
                            buy_logic_rules,
                            key=lambda x: int(x.get("price_larger_then", 0)),
                            reverse=False,
                        )

                        quantity_to_buy = int(
                            self.sequence_settings.get("default_buy_amount", 0)
                        )

                        for rule in rules_sorted:
                            price_threshold = int(rule.get("price_larger_then"))
                            if int(lowest_price) > price_threshold:
                                quantity_to_buy = int(rule.get("amount_to_buy"))

                        if quantity_to_buy > 0:
                            print(
                                f"Profitable Order for {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Qty: {quantity_to_buy}"
                            )
                            self.logger.add_log(
                                "orders",
                                f"Placing Order {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Qty: {quantity_to_buy} | Silver: {self.sniffer.current_silver}",
                            )
                            # Create Buy Order (fast_buy=False means +1 silver logic usually, or explicit price)
                            self.market_manager.buy_item(
                                amount=quantity_to_buy,
                                fast_buy=False,
                                fast_buy_price=0 
                            )
                            self.add_recent_item(
                                self.market_manager.get_name_from_unique(item_unique_name),
                                f"{int(lowest_price)} x{quantity_to_buy}",
                                "order",
                            )
                        else:
                            print(f"Item {item_unique_name} profitable but quantity filtered by logic.")
                            self.market_manager.close_item()
                    else:
                        self.market_manager.close_item()

                if (
                    self.sniffer.current_silver != 0
                    and int(self.min_silver) >= self.sniffer.current_silver
                ):
                    print("[Warning] Silver amount is less than minimum to continue")
                    self.logger.add_log(
                        "orders",
                        "[Warning] Silver amount is less than minimum to continue",
                    )
                    break
        except Exception as e:
            print(f"[Error] Buy items issue: {e}")
            self.logger.add_log("error", f"[Error] Buy items issue: {e}")
        self.status = "Ready"

    def sell_items(self):
        self.status = "Running"
        self.current_task_name = "Selling Items"
        self.capture.set_foreground_window()
        market_title = self.market_manager.get_market_title()
        self.current_location = market_title
        try:
            self.logger.add_log(
                "orders",
                "Starting to make sell orders",
            )
            self.market_manager.prepare_for_sell(market_title)
            self.sniffer.clear_market_buffer()
            self.market_manager.sleep(.2)
            self.market_manager.open_item()
            self.market_manager.sleep(.3)

            current_offers, current_requests = self.sniffer.get_market_buffer() 

            while (len(current_offers) != 0 or len(current_requests) != 0):
                self.update_market_prices(market_title, offers=current_offers, requests=current_requests)
                self._wait_if_paused()
                fast_sale_price = 0
                if len(current_requests) != 0:
                    for order in current_requests:
                        if order.get("AuctionType") == "request":
                            price = order.get("UnitPriceSilver", 0) / 10000
                            if price > fast_sale_price and price > 0:
                                fast_sale_price = price
                else:
                    fast_sale_price = 0

                order_sale_price = float('inf')
                if len(current_offers) != 0:
                    for order in current_offers:
                        if order.get("AuctionType") == "offer":
                            price = order.get("UnitPriceSilver", 0) / 10000
                            if price < order_sale_price and price > 0:
                                order_sale_price = price
                else:
                    order_sale_price = 1
                
                if fast_sale_price == 0:
                    self.market_manager.make_sell_order()
                elif (fast_sale_price != 0 and order_sale_price != 0) and (fast_sale_price/order_sale_price) > 0.85:
                    self.market_manager.fast_sale_item()
                else:
                    self.market_manager.make_sell_order()
                
                self.sniffer.clear_market_buffer()
                self.market_manager.sleep(.2)
                self.market_manager.open_item()
                self.market_manager.sleep(.2)
                current_offers, current_requests = self.sniffer.get_market_buffer()
                self.market_manager.sleep(.1)
            self.logger.add_log(
                "orders",
                "Sell orders Done!",
            )
        except Exception as e:
            self.logger.add_log("market", f"Error while sell items: {e}")
        self.status = "Ready"

    def travel_to(self, destination: str):
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Traveling"
        self.logger.add_log("travel", f"Bot Starting traveling to {destination}")
        self.capture.set_foreground_window()
        change_keyboard_layout()
        self.overlay.stop()
        self.travel_manager.travel_to(destination=destination)

    def check_login(self):
        self.login_manager.check_login()


if __name__ == "__main__":
    bot = Bot()
    bot.sell_item_bm()