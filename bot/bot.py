import os
import re
import json
import threading
import asyncio
import traceback
import win32con, win32gui, win32api
from .core import WindowCapture
from .core.input import BotStopped
from .api import DatabaseInterface
from .net import Sniffer
from .classes import LocalPlayer
from .handlers import SettingsHandler, TravelHandler, MarketHandler, LoginHandler, LogHandler, ChestHandler

def change_keyboard_layout(language_id_hex=0x04090409):
    hwnd = win32gui.GetForegroundWindow()

    if hwnd:
        win32api.PostMessage(
            hwnd, win32con.WM_INPUTLANGCHANGEREQUEST, 0, language_id_hex
        )
    else:
        print("No active window found.")


class Bot:
    def __init__(self, sniffer: Sniffer, settings: SettingsHandler, overlay, local_player: LocalPlayer):
        self.sniffer = sniffer
        self.settings = settings
        self.capture = WindowCapture("Albion Online Client")
        self.overlay = overlay
        self.db = DatabaseInterface()
        self.log_handler = LogHandler()
        self.login_handler = LoginHandler()
        self.market_handler = MarketHandler(self, self.capture, self.settings)
        self.chest_handler = ChestHandler(self.capture, self.settings)

        self.local_player = local_player
        self.sniffer.subscribe_silver(self.local_player.on_silver_changed)
        self.sniffer.subscribe_position(self.local_player.on_position_changed)
        self.sniffer.subscribe_nickname(self.local_player.on_nickname_changed)
        self.sniffer.subscribe_location(self.local_player.on_location_changed)
        self.sniffer.subscribe_new_item(self.local_player.on_new_item)

        self.travel_handler = TravelHandler(self, self.capture, self.settings, self.local_player)
        self.sniffer.subscribe_location(self.travel_handler.on_location_changed)
        self.sniffer.subscribe_join(self.travel_handler.on_join_finished)

        self._can_run = threading.Event()
        self._can_run.set()
        self._stop_requested = False 

        stop_check = lambda: self._stop_requested
        self.market_handler.set_stop_callback(stop_check)
        self.travel_handler.set_stop_callback(stop_check)
        self.chest_handler.set_stop_callback(stop_check)

        self.status = "Alive"
        self.current_task_name = ""
        self.recent_items = []

        self.log_handler.add_log("bot", f"Bot initialized!")

    def get_status(self):
        status = self.status
        if self.local_player.location.location_id == "":
            status = "Change Location"
        return status

    async def _run_task(self, func, *args, **kwargs):
        self._stop_requested = False
        self.resume()
        try:
            await self._wait_for_resume()
            await func(*args, **kwargs)
        except BotStopped:
            print(f"[Bot] Task '{func.__name__}' was stopped by user.")
        except Exception as e:
            print(f"[Bot] Error in task '{func.__name__}': {e}")
            traceback.print_exc()

    async def _wait_for_resume(self):
        while not self._can_run.is_set():
            if self._stop_requested:
                return
            await asyncio.sleep(0.5)

    def _load_preset_items(self, city: str):
        buy_mode = self.settings.get("general")["buy_mode"]
        preset_file = self.settings.get(buy_mode+"_buy")["presets"][city]
        if not preset_file:
            print(f"[Error] No preset selected for '{city}'")
            self.log_handler.add_log("error", f"[Error] No preset selected for '{city}'")
            return []

        path = os.path.join(self.settings.PRESETS_DIR, preset_file)
        if not os.path.exists(path):
            print(f"[Error] Preset file not found: {path}")
            self.log_handler.add_log("error", f"[Error] Preset file not found: {path}")
            return []

        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Failed to load preset {preset_file}: {e}")
            self.log_handler.add_log(
                "error", f"[Error] Failed to load preset {preset_file}: {e}"
            )
            return []

    def _parse_item_info(self, full_unique_name: str):
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

    def _update_overlay(self):
        if self.overlay:
            self.overlay.send_update(
                status=self.status,
                task=self.current_task_name,
                paused=not self._can_run.is_set(),
                recent_items=self.recent_items,
            )

    def _add_recent_item(self, name, price, type="check"):
        self.recent_items.insert(0, {"name": name, "price": str(price), "type": type})
        if len(self.recent_items) > 5:
            self.recent_items.pop()
        self._update_overlay()

    def _calculate_price_extremum(self, orders: list[dict], find_min=True):
        found_prices = {}
        for order in orders:
            quality = order.get("QualityLevel", 1)
            if quality > 3:
                continue

            full_name = order.get("ItemTypeId", "Unknown")
            base_name, tier, enchant = self._parse_item_info(full_unique_name=full_name)
            raw_price = order.get("UnitPriceSilver", 0)
            key = (base_name, tier, enchant)

            if key not in found_prices:
                found_prices[key] = raw_price
            else:
                if find_min:
                    if raw_price < found_prices[key]:
                        found_prices[key] = raw_price
                else:
                    if raw_price > found_prices[key]:
                        found_prices[key] = raw_price
        return found_prices

    def _update_market_prices(self, market_title, offers=None, requests=None):
        """
        Updates database prices based on market buffers according to user rules.
        
        NEW RULE:
        - OFFERS (Sell Orders) -> Update into 'fast' datatable (using MIN price)
        - REQUESTS (Buy Orders) -> Update into 'order' datatable (using MAX price)
        
        Returns a tuple of dicts ({unique_name: price}, {unique_name: price}) for offers and requests.
        """
        updated_offers = {}
        updated_requests = {}
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
                    self.db.update_item_prices(payload, item_type="fast")

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
                    self.db.update_item_prices(payload, item_type="order")
        
        return updated_offers, updated_requests

    def _filter_bought_items(self, orders_list: list[dict], items_to_buy: list[str]):
        existing_order_ids = {order.get('ItemTypeId') for order in orders_list}
        remaining_items = [item for item in items_to_buy if item not in existing_order_ids]
        return remaining_items

    def _get_black_market_price(self, item_unique_name: str, items_prices_fast: dict, items_prices_order: dict) -> int | None:
        black_market_price_fast = items_prices_fast.get(item_unique_name, 0)/10000
        black_market_price_order = items_prices_order.get(item_unique_name, 0)/10000

        if black_market_price_fast == 0 and black_market_price_order == 0:
            print(f"No black market data for {item_unique_name}")
            self.log_handler.add_log("orders", f"No black market data for {item_unique_name}")
            return None

        return max(black_market_price_fast, black_market_price_order)

    def _get_amount_to_buy(self, price: int) -> int:
        buy_logic_rules = [
            i for i in self.sequence_settings.get("buy_logic", [])
            if i["amount_to_buy"] != "" and i["price_larger_then"] != ""
        ]
        rules_sorted = sorted(
            buy_logic_rules,
            key=lambda x: int(x.get("price_larger_then", 0)),
            reverse=False
        )
        quantity_to_buy = int(self.sequence_settings.get("default_buy_amount", 0))

        for rule in rules_sorted:
            price_threshold = int(rule.get("price_larger_then"))
            if price > price_threshold:
                quantity_to_buy = int(rule.get("amount_to_buy"))

        return quantity_to_buy

    async def _check_bm_from_inventory(self):
        try:
            for x in range(6):
                self.overlay.stop()
                await self.travel_handler.move_to_guild_chest()
                if x == 0:
                    self.chest_handler.take_mount()
                    self.chest_handler.sleep(.5)
                    self.chest_handler.take_items_from_tab()
                elif x == 5:
                    self.chest_handler.stash_item_into_tab()
                    self.chest_handler.sleep(.5)
                    self.chest_handler.stash_mount()
                    self.chest_handler.sleep(.5)
                    self.chest_handler.from_tab_to_tab()
                    continue
                else:
                    self.chest_handler.stash_item_into_tab()
                    self.chest_handler.sleep(.5)
                    self.chest_handler.take_items_from_tab()
                
                self.local_player.clear_inventory()
                await self.travel_handler.move_to_market("3003")
                self.market_handler.sleep(2)
                self.market_handler.change_tab("sell")
                market_title = self.market_handler.get_market_title()
                self.log_handler.add_log("bot", f"Bot Starting order price checking for {market_title}")
                inventory_items = list(self.local_player.get_inventory().values())
                self.overlay.start()
                self.market_handler.sleep(2)
                for i, item in enumerate(inventory_items):
                    await self._wait_for_resume()
                    item_name = self.market_handler.get_name_from_index(str(item))
                    self.current_item_name = f"Scanning: {item_name}"
                    self.current_task_name = (f"Cheking Price: {i+1}/{len(inventory_items)}")
                    self._update_overlay()

                    self.market_handler.search_item(item_name, black_market=True)
                    self.market_handler.open_item()
                    self.market_handler.sleep(0.3)
                    self.market_handler.check_all_item_orders(minimal_item_tier=self.settings.SPECIAL_ITEMS_BM.get(str(item), 4))
                    self.market_handler.close_item()

                    current_offers, current_requests = self.sniffer.get_market_buffers()
                    if not current_offers and not current_requests:
                        self.log_handler.add_log("market", f"No market data captured for: {item} (price_check)")
                        self._add_recent_item(item, "N/A", "check")

                    updated_offers, updated_requests = self._update_market_prices(
                        market_title, offers=current_offers, requests=current_requests
                    )

                    if updated_offers:
                        self._add_recent_item(item, f"fast updated!", "check")
                        self.log_handler.add_log("market", f"{item_name} fast price checked")
                    if updated_requests:
                        self._add_recent_item(item, f"order updated!", "check")
                        self.log_handler.add_log("market", f"{item_name} order price checked")
                self.db.force_price_update()
                await self.travel_handler.move_to_island("Matvey4a Guild's Island - Caerleon")
        except Exception as e:
            self.log_handler.add_log("market", f"Order BM price cheking Error: {e}")

    def stop(self):
        print("[Bot] Stopping...")
        self._stop_requested = True
        self._can_run.clear()

        self.travel_handler.release_all_keys()
        self.travel_handler.can_move = True
        print("[Bot] Stopped")

    def pause(self):
        print("[Bot] pausing...")
        self._can_run.clear()

    def resume(self):
        change_keyboard_layout()
        print("[Bot] resuming...")
        self._can_run.set()

    def toggle_pause(self):
        if self._can_run.is_set():
            self.pause()
            return True
        else:
            self.resume()
            return False

    async def travel_to(self, destination: str):
        change_keyboard_layout()
        await self._wait_for_resume()
        self.recent_items = []
        self.status = "Running"
        self.current_task_name = "Traveling"
        self.log_handler.add_log("travel", f"Bot Starting traveling to {destination}")
        self.capture.set_foreground_window()
        self.overlay.stop()
        
        if destination in self.settings.MARKET_TITLES.keys():
            await self.travel_handler.move_to_market(destination)
        else:
            await self.travel_handler.move_to_island(destination)

    async def check_price_fast(self):
        try:
            change_keyboard_layout()
            self.capture.set_foreground_window()
            self.recent_items = []
            self.status = "Running"
            market_title = self.market_handler.get_market_title()
            self.log_handler.add_log("bot", f"Bot Starting price checking for {market_title}")
            is_black_market = market_title == "black_market"
            self.overlay.start()
            self.market_handler.sleep(2)

            if is_black_market:
                items_to_check = list(self.settings.ITEMS_BLACK_MARKET.values())
            else:
                items_to_check = self._load_preset_items(market_title)
                if not items_to_check:
                    return
                
            self.current_task_name = f"Cheking Price: 0/{len(items_to_check)}"
            self.market_handler.change_tab("buy")
            self._update_overlay()

            for i, item in enumerate(items_to_check):
                await self._wait_for_resume()
                self.current_item_name = f"Scanning: {item}"
                self.current_task_name = (f"Cheking Price: {i+1}/{len(items_to_check)}")
                self._update_overlay()

                if is_black_market:
                    self.market_handler.search_item(item, black_market=True)
                else:
                    self.market_handler.search_item(item, from_db=True)

                self.market_handler.sleep(0.3)
                self.market_handler.check_pages()
                current_offers, current_requests = self.sniffer.get_market_buffers()
                
                if not current_offers and not current_requests:
                    self.log_handler.add_log(
                        "market", f"No market data captured for: {item} (price_check)"
                    )
                    self._add_recent_item(item, "N/A", "check")

                updated_offers, updated_requests = self._update_market_prices(
                    market_title, offers=current_offers, requests=current_requests
                )

                if updated_offers:
                    self._add_recent_item(item, f"fast updated!", "check")
                    self.log_handler.add_log("market", f"{item} fast price checked")
                if updated_requests:
                    self._add_recent_item(item, f"order updated!", "check")
                    self.log_handler.add_log("market", f"{item} order price checked")
            self.db.force_price_update()
        except Exception as e:
            self.log_handler.add_log("market", f"Error while Fast Sell price checking: {e}")

    async def check_price_orders(self):
        try:
            change_keyboard_layout()
            self.capture.set_foreground_window()
            self.status = "Running"
            self.current_task_name = f"Checking Price: 0/X"
            market_title = self.market_handler.get_market_title()
            self.overlay.start()
            self._update_overlay()
            self.market_handler.sleep(2)
            if market_title not in self.settings.MARKET_TITLES.values():
                await self._check_bm_from_inventory()
                return
            elif market_title == "black_market":
                await self.travel_to("Matvey4a Guild's Island - Caerleon")
                await self.check_price_orders()
                return
            
            self.market_handler.sleep(.5)
            self.market_handler.change_tab("buy")
            self.log_handler.add_log("bot", f"Bot Starting order price checking for {market_title}")
            items_to_check = list(self.settings.ITEMS_BLACK_MARKET.values())
            self.market_handler.prepare(True)

            for i, item in enumerate(items_to_check):
                await self._wait_for_resume()
                item_name = item
                self.current_item_name = f"Scanning: {item_name}"
                self.current_task_name = (f"Cheking Price: {i+1}/{len(items_to_check)}")
                self._update_overlay()

                self.market_handler.search_item(item_name, black_market=True)
                self.market_handler.open_item()
                self.market_handler.sleep(0.3)
                self.market_handler.check_all_item_orders(
                    minimal_item_tier=self.settings.SPECIAL_ITEMS.get(str(item), 4)
                )
                self.market_handler.close_item()

                current_offers, current_requests = self.sniffer.get_market_buffers()

                if not current_offers and not current_requests:
                    print(f"No market data captured for: {item}")
                    self.log_handler.add_log("market", f"No market data captured for: {item} (price_check)")
                    self._add_recent_item(item, "N/A", "check")

                updated_offers, updated_requests = self._update_market_prices(
                    market_title, offers=current_offers, requests=current_requests
                )

                if updated_offers:
                    self._add_recent_item(item, f"fast updated!", "check")
                    self.log_handler.add_log("market", f"{item_name} fast price checked")
                if updated_requests:
                    self._add_recent_item(item, f"order updated!", "check")
                    self.log_handler.add_log("market", f"{item_name} order price checked")

            self.db.force_price_update()
        except Exception as e:
            self.log_handler.add_log("market", f"Order price cheking Error: {e}")

    async def buy_items(self, items_to_buy_list: list = None, buy_mode: str = None):
        try:
            change_keyboard_layout()
            self.capture.set_foreground_window()
            self.recent_items = []
            self.status = "Running"
            self.current_task_name = "Loading Prices"
            self.overlay.start()
            self._update_overlay()
            self.market_handler.sleep(2)
            market_title = self.market_handler.get_market_title()
            if buy_mode == None:
                buy_mode = self.settings.get("general")["buy_mode"]
            if items_to_buy_list == None:
                items_to_buy_list = self._load_preset_items(market_title)
            is_fast_buy = buy_mode == "fast"
            items_prices_order = self.db.get_all_prices_for_city("black_market", item_type="fast")
            items_prices_fast = self.db.get_all_prices_for_city("black_market", item_type="order")
            self.current_task_name = "Buying Items"
            self._update_overlay()

            if not items_to_buy_list:
                print("No items to buy. Please select a preset in Settings")
                self.log_handler.add_log("market", f"No itmes to buy. Please select a preset in Settings")
                return

            self.log_handler.add_log("market", f"Starting Buying {len(items_to_buy_list)} items in {market_title}")
            self.market_handler.prepare()
            
            for i, item_unique_name in enumerate(items_to_buy_list):
                await self._wait_for_resume()
                self.settings.reload_settings()
                # Reload settings here to catch changes during pause/resume
                self.min_silver = self.settings.get("general")["min_silver"]
                self.sequence_settings = self.settings.get(f"{buy_mode}_buy")

                self.current_task_name = f"Buy Items: {i+1}/{len(items_to_buy_list)}"
                self._update_overlay()

                self.sniffer.clear_market_buffers()
                self.market_handler.search_item(item_unique_name, True, False)
                self.market_handler.open_item()
                self.market_handler.sleep(.5)
                
                current_offers, current_requests = self.sniffer.get_market_buffers()
                self._update_market_prices(market_title, current_offers, current_requests)
                if (len(current_offers) == 0 and len(current_requests) == 0):
                    print(f"No data for {item_unique_name}")
                    self.log_handler.add_log("orders", f"No data for {item_unique_name}")
                    if is_fast_buy:
                        self.market_handler.close_item()
                        continue

                black_market_price = self._get_black_market_price(item_unique_name, items_prices_fast, items_prices_order)
                min_profit_rate = float(self.sequence_settings["min_profit_rate"]) / 100 or 0.0

                if black_market_price == None:
                    self.market_handler.close_item()
                    continue

                if is_fast_buy:
                    if not current_offers:
                        self.market_handler.close_item()
                        continue

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

                        temp_cost = cumulative_cost + (price * amount)
                        temp_qty = cumulative_qty + amount
                        avg_price = temp_cost / temp_qty

                        profit = black_market_price * 0.96 - avg_price
                        profit_margin = (profit / avg_price) if avg_price > 0 else 0

                        if profit_margin >= min_profit_rate:
                            cumulative_cost = temp_cost
                            cumulative_qty = temp_qty
                            final_buy_qty = cumulative_qty
                            final_max_price = price
                            final_avg_price = avg_price
                            final_profit_margin = profit_margin
                        else:
                            break

                    final_buy_qty = min(final_buy_qty, self._get_amount_to_buy(final_avg_price))
                    if final_buy_qty > 0:
                        self.log_handler.add_log("orders", f"Buying Batch {item_unique_name} | Qty: {final_buy_qty} | Avg: {final_avg_price:.2f} | Max: {final_max_price} | Margin: {final_profit_margin*100:.2f}% | Silver: {self.local_player.silver_balance}")
                        self.market_handler.buy_item(
                            amount=final_buy_qty,
                            fast_buy=True,
                            fast_buy_price=int(final_max_price)
                        )
                        self._add_recent_item(
                            self.market_handler.get_name_from_unique(item_unique_name),
                            f"~{int(final_avg_price)} x{final_buy_qty}",
                            "buy",
                        )
                    else:
                        self.market_handler.close_item()
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
                        quantity_to_buy = self._get_amount_to_buy(lowest_price)
                        if quantity_to_buy > 0:
                            self.log_handler.add_log("orders", f"Placing Order {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Qty: {quantity_to_buy} | Silver: {self.local_player.silver_balance}")
                            self.market_handler.buy_item(
                                amount=quantity_to_buy,
                                fast_buy=False,
                                fast_buy_price=0 
                            )
                            self._add_recent_item(
                                self.market_handler.get_name_from_unique(item_unique_name),
                                f"{int(lowest_price)} x{quantity_to_buy}",
                                "order",
                            )
                        else:
                            self.market_handler.close_item()
                    else:
                        self.market_handler.close_item()
                if self.local_player.silver_balance != 0 and int(self.min_silver) >= self.local_player.silver_balance:
                    self.log_handler.add_log("orders", "[Warning] Silver amount is less than minimum to continue")
                    break
        except Exception as e:
            self.log_handler.add_log("error", f"[Error] Buy items issue: {e}")

    async def update_orders(self):
        try:
            change_keyboard_layout()
            self.capture.set_foreground_window()
            self.status = "Running"
            self.current_task_name = "Price Loading"
            self.overlay.start()
            self._update_overlay()
            self.market_handler.sleep(2)

            market_title = self.market_handler.get_market_title()
            self.log_handler.add_log("market", f"Bot Starting to update existing orders for {market_title}")
            items_to_buy_list = self._load_preset_items(market_title)
            items_prices_order = self.db.get_all_prices_for_city("black_market", item_type="fast")
            items_prices_fast = self.db.get_all_prices_for_city("black_market", item_type="order")

            self.current_task_name = "Orders Update"
            self._update_overlay()

            if not items_to_buy_list:
                print("No items to buy. Please select a preset in Settings")
                self.log_handler.add_log("market", f"No itmes to buy. Please select a preset in Settings")
                return
            
            self.market_handler.prepare_for_order_update()
            self.sniffer.clear_market_buffers()
            self.market_handler.sleep(.3)
            self.market_handler.reset_my_orders()
            orders_exists = []
            temp_orders_exists = self.sniffer.get_market_buffers("request")
            while len(temp_orders_exists) != 0:
                orders_exists.extend(temp_orders_exists)
                self.market_handler.next_my_orders_page()
                self.market_handler.sleep(.2)
                temp_orders_exists = self.sniffer.get_market_buffers("request")
                self.market_handler.sleep(.2)
            self.market_handler.prepare_for_order_update()
            my_nickname = self.local_player.nickname if self.local_player.nickname != "" else orders_exists[0].get("BuyerName")
            for i, exist_order in enumerate(orders_exists):
                await self._wait_for_resume()
                self.settings.reload_settings()
                # Reload settings here to catch changes during pause/resume
                self.min_silver = self.settings.get("general")["min_silver"]
                self.sequence_settings = self.settings.get(f"order_buy")

                item_unique_name = exist_order.get("ItemTypeId")
                self.current_task_name = f"Updating Orders: {i+1}/{len(orders_exists)}"
                self._update_overlay()

                self.market_handler.search_item(item_unique_name, True, False)
                self.market_handler.sleep(.2)                
                self.sniffer.clear_market_buffers()
                self.market_handler.reset_my_orders()
                for i, order in enumerate(self.sniffer.get_market_buffers("request")):
                    if order.get("ItemTypeId") == item_unique_name:
                        self.market_handler.open_item(True, i+1)
                self.market_handler.sleep(.3)
                current_offer, current_requests = self.sniffer.get_market_buffers()
                if len(current_offer) == 0 and len(current_requests) == 0:
                    self.market_handler.close_item()
                    continue

                black_market_price = self._get_black_market_price(item_unique_name, items_prices_fast, items_prices_order)
                self._update_market_prices(market_title, current_offer, current_requests)
                if black_market_price == None and current_buyer != my_nickname:
                    self.market_handler.close_item()
                    self.market_handler.remove_order(1)
                    continue

                if len(current_requests) != 0:
                    lowest_price = float("inf")
                    order_price = 1
                    current_amount = 0
                    current_buyer = ""
                    for order in current_requests:
                        if order.get("ItemTypeId") == item_unique_name:
                            order_buyer = order.get("BuyerName", "")
                            if order_buyer == my_nickname:
                                current_amount = int(order.get("Amount"))
                            price = order.get("UnitPriceSilver", 0)/10000
                            if price > order_price and price > 0:
                                order_price = price
                                current_buyer = order_buyer
                    lowest_price = int(order_price)
                    if current_buyer == my_nickname:
                        self.market_handler.close_item()
                        continue

                    profit = black_market_price * 0.96 - lowest_price
                    profit_margin = (profit / lowest_price) if lowest_price > 0 else profit
                    min_profit_rate = float(self.sequence_settings["min_profit_rate"]) / 100 or 0.0
                    if profit_margin >= min_profit_rate:
                        quantity_to_buy = self._get_amount_to_buy(lowest_price)
                        if quantity_to_buy > 0:
                            self.log_handler.add_log(
                                "orders",
                                f"Placing Order {item_unique_name} | Price: {lowest_price} | Margin: {profit_margin*100:.2f}% | Qty: {quantity_to_buy} | Silver: {self.local_player.silver_balance}",
                            )
                            self.market_handler.buy_item(
                                amount=(quantity_to_buy-current_amount+1),
                                fast_buy=True,
                                fast_buy_price=int(lowest_price+1)
                            )
                            self._add_recent_item(
                                self.market_handler.get_name_from_unique(item_unique_name),
                                f"{int(lowest_price+1)} x{quantity_to_buy}",
                                "order"
                            )
                    else:
                        self.market_handler.close_item()
                        self.market_handler.remove_order(1)
                else:
                    self.market_handler.close_item()

                if self.local_player.silver_balance != 0 and int(self.min_silver) >= self.local_player.silver_balance:
                    self.log_handler.add_log("orders", "[Warning] Silver amount is less than minimum to continue")
                    break
            if self.local_player.silver_balance != 0 and int(self.min_silver) >= self.local_player.silver_balance:
                self.log_handler.add_log("orders", "[Warning] Silver amount is less than minimum to continue")
                return
            
            self.market_handler.prepare_for_order_update()
            self.sniffer.clear_market_buffers()
            self.market_handler.sleep(.3)
            self.market_handler.reset_my_orders()
            orders_exists = []
            temp_orders_exists = self.sniffer.get_market_buffers("request")
            while len(temp_orders_exists) != 0:
                orders_exists.extend(temp_orders_exists)
                self.market_handler.next_my_orders_page()
                self.market_handler.sleep(.2)
                temp_orders_exists = self.sniffer.get_market_buffers("request")
                self.market_handler.sleep(.2)

            final_buy_list = self._filter_bought_items(orders_exists, items_to_buy_list)
            await self.buy_items(final_buy_list)
        except Exception as e:
            self.log_handler.add_log("market", f"Error while updating orders: {e}")

    async def remove_orders(self):
        try:
            change_keyboard_layout()
            self.capture.set_foreground_window()
            self.sniffer.clear_market_buffers()
            self.recent_items = []
            self.status = "Running"
            self.current_task_name = "Removing Orders"
            self.overlay.start()
            self._update_overlay()
            self.market_handler.sleep(2)

            market_title = self.market_handler.get_market_title()
            self.log_handler.add_log("bot", f"Bot Starting to remove orders for {market_title}")
            self.market_handler.change_tab("my_orders_tab")
            self.market_handler.remove_order(12)
            self.market_handler.scroll()
            requests = len(self.sniffer.get_market_buffers("request"))
            while requests != 0:
                await self._wait_for_resume()
                self.market_handler.reset_my_orders()
                self.market_handler.remove_order(12)
                self.market_handler.scroll()
                requests = len(self.sniffer.get_market_buffers("request"))
        except Exception as e:
            self.log_handler.add_log("market", f"Error while removing orders: {e}")

    async def sell_items(self):
        try:
            change_keyboard_layout()
            self.status = "Running"
            self.current_task_name = "Selling Items"
            self.overlay.start()
            self._update_overlay()
            self.market_handler.sleep(2)
            
            market_title = self.market_handler.get_market_title()
            self.capture.set_foreground_window()
            self.log_handler.add_log("orders", "Starting to make sell orders")

            self.market_handler.prepare_for_sell(market_title)
            self.sniffer.clear_market_buffers()
            self.market_handler.sleep(.2)
            self.market_handler.open_item()
            self.market_handler.sleep(.3)

            current_offers, current_requests = self.sniffer.get_market_buffers()
            while (len(current_offers) != 0 or len(current_requests) != 0):
                self._update_market_prices(market_title, offers=current_offers, requests=current_requests)
                await self._wait_for_resume()
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

                if (fast_sale_price != 0 and order_sale_price != 1) and (fast_sale_price/order_sale_price) > 0.95:
                    self.market_handler.fast_sale_item()
                elif order_sale_price == 1:
                    sell_price = self.sniffer.get_last_avg_price()
                    if sell_price == 0:
                        if fast_sale_price != 0:
                            self.market_handler.make_sell_order(order_price=int(fast_sale_price*1.05))
                        else:
                            self.market_handler.make_sell_order(order_price=9999)
                    else:
                        self.market_handler.make_sell_order(order_price=sell_price)
                else:
                    self.market_handler.make_sell_order()
                
                self.sniffer.clear_market_buffers()
                self.market_handler.sleep(.2)
                self.market_handler.open_item()
                self.market_handler.sleep(.2)
                current_offers, current_requests = self.sniffer.get_market_buffers()
                self.market_handler.sleep(.1)
            self.db.force_price_update()
            self.log_handler.add_log("orders", "Sell orders Done!")
        except Exception as e:
            self.log_handler.add_log("market", f"Error while sell items: {e}")
