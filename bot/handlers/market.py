from ..core import WindowCapture, InputSender
from .settings import SettingsHandler
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import Bot


class MarketHandler(InputSender):
    def __init__(self, bot: "Bot", capture: WindowCapture, settings: SettingsHandler):
        super().__init__()
        self.bot = bot
        self.capture = capture
        self.settings = settings

        self.resolution = capture.get_window_resolution()
        w_h = self.resolution.split("x")
        self.width, self.height = int(w_h[0]), int(w_h[1])
        self.capture_positions = self.settings.CAPTURE_POSITIONS[self.resolution]["market"]
        self.mouse_positions = self.settings.MOUSE_POSITIONS[self.resolution]["market"]
        self.items = {item["UniqueName"]: item for item in self.settings.ITEM_DATA}
        self.items_idx = {item["Index"]: item for item in self.settings.ITEM_DATA}
        self.lang = "EN-US"

    def get_name_from_unique(self, unique_name: str) -> str | None:
        if unique_name in self.items:
            return self.items[unique_name]["LocalizedNames"].get(self.lang, "Language not found")
        return None
    
    def get_name_from_index(self, name_index: str) -> str | None:
        if name_index in self.items_idx:
            return self.items_idx[name_index]["LocalizedNames"].get(self.lang, "Language not found")
        return None
    
    def get_market_title(self) -> str | None:
        location_id = self.bot.local_player.location.location_id
        market_title = self.settings.MARKET_TITLES.get(location_id)
        if market_title == None:
            raw_title = self.capture.get_text_from_screenshot(self.capture_positions["title"]).replace("marketplace", "")
            if "fort" in raw_title:
                return "fort_sterling"
            elif "lymhurst" in raw_title:
                return "lymhurst"
            elif "bridgewatch" in raw_title:
                return "bridgewatch"
            elif "martlock" in raw_title:
                return "martlock"
            elif "thetford" in raw_title:
                return "thetford"
            elif "brecilien" in raw_title:
                return "brecilien"
            elif "black" in raw_title:
                return "black_market"
            elif "caerleon" in raw_title:
                return "caerleon"
            else:
                return None
        return market_title
    
    def change_tier(self, tier: int) -> str | None:
        self.click(self.mouse_positions["tier"])
        self.sleep(.1)
        self.click(self.mouse_positions[f"tier_{tier}"])
        self.sleep(.1)
    
    def remove_order(self, amount: int = 10):
        self.click(self.mouse_positions["button_remove_order"], amount, interval=0.1)

    def check_pages(self, clicks: int = 6) -> None:
        self.click(self.mouse_positions["next_page"], clicks=clicks, interval=0.2)
        self.sleep(0.5)

    def check_item_stats(self) -> None:
        if self.capture.get_text_from_screenshot(self.capture_positions["stats"]) != "sell orders":
            self.click(self.mouse_positions["button_extend_item_statistic"])
            self.sleep(0.5)

    def check_all_item_orders(self, minimal_item_tier: int = 4):
        self.click(self.mouse_positions["button_opened_quality"])
        self.click(self.mouse_positions["button_opened_quality_good"])
        for x in range(5 - minimal_item_tier):
            self.click(self.mouse_positions["button_opened_tier"])
            self.click(self.mouse_positions[f"button_opened_tier_{x+2}"])
        for y in range(5):
                self.click(self.mouse_positions["button_opened_enchantment"])
                self.click(self.mouse_positions[f"button_opened_enchantment_{y}"])
        for i in range(4):
            self.click(self.mouse_positions["button_opened_tier"])
            self.click(self.mouse_positions[f"button_opened_tier_{i+3}"])
            for j in range(5):
                self.click(self.mouse_positions["button_opened_enchantment"])
                self.click(self.mouse_positions[f"button_opened_enchantment_{j}"])
    
    def search_item(self, name: str, from_db: bool = False, black_market: bool = False) -> None:
        tier = name.split("_")[0][1]
        enchant = "0"
        if name.split("@")[-1][0] != "T":
            enchant = name.split("@")[-1][0]

        if from_db == True:
            name_from_unique = self.get_name_from_unique(name)
            if name_from_unique is not None:
                name = name_from_unique
                     
        self.click(self.mouse_positions["search_reset"])
        pos = self.mouse_positions["search"]
        self.click([pos[0]+random.randint(1, int(self.width/16)), pos[1]])
        if black_market == False:
            name = name+f" {tier}_{enchant}"
        self.typewrite(name)
        self.sleep(0.3)

    def change_tab(self, name: str) -> None:
        self.click(self.mouse_positions["tab_"+name])
        self.sleep(0.5)

    def open_item(self, isEditOrder: bool = False, item_index = 1) -> None:
        if isEditOrder:
            self.click(self.mouse_positions[f"button_edit_my_order_{item_index}"])
        else:
            self.click(self.mouse_positions["button_buy"])
        self.check_item_stats()
        self.sleep(0.5)

    def close_item(self) -> None:
        self.click(self.mouse_positions["button_close_order_popup"])
        self.sleep(0.5)

    def buy_item(self, amount: int = 10, fast_buy: bool = False, fast_buy_price: int = 1) -> None:
        self.click(self.mouse_positions["button_buy_order"])
        self.click(self.mouse_positions["button_change_amount"])
        if amount > 0:
            self.click(self.mouse_positions["button_amount_more"], clicks=amount-1)
        elif amount < 0:
            self.click(self.mouse_positions["button_amount_less"], clicks=abs(amount)-1)

        if fast_buy == True:
            self.click(self.mouse_positions["button_change_price"])
            self.typewrite(fast_buy_price)
        else:
            self.click(self.mouse_positions["button_one_silver_more"])

        self.click(self.mouse_positions["button_create_order"])
        self.sleep(0.2)
        self.click(self.mouse_positions["button_crate_order_confirmation"])
        self.sleep(0.1)

        self.sleep(0.5)

    def prepare(self, isPriceCheck: bool = False):
        self.change_tab("buy")
        self.reset_filters()
        self.click(self.mouse_positions["quality"])
        self.click(self.mouse_positions["quality_good"])
        if isPriceCheck: self.change_tier(4)
        self.change_tab("create_buy_order")

    def prepare_for_sell(self, market_title: str = "black_market"):
        if market_title == "black_market":
            self.change_tab("sell")
            self.sleep(0.2)
            self.reset_filters()

    def prepare_for_order_update(self):
        self.change_tab("create_buy_order")
        self.sleep(.2)
        self.change_tab("my_orders_tab")
        self.sleep(.2)
        self.reset_filters()
        self.sleep(.3)

    def reset_filters(self):
        self.click(self.mouse_positions["category_reset"])
        self.click(self.mouse_positions["search_reset"])

    def fast_sale_item(self, market_title: str = "black_market"):
        if market_title == "black_market":
            self.click(self.mouse_positions["opened_item_sell_bm"])
            self.sleep(.1)
        self.click(self.mouse_positions["button_create_order"])
        self.sleep(.1)

    def make_sell_order(self, market_title: str = "black_market", order_price: int = 0):
        if market_title == "black_market":
            self.click(self.mouse_positions["opened_item_sell_order_bm"])
        self.sleep(.1)

        if order_price == 0:
            self.click(self.mouse_positions["button_one_silver_less"])
        else:
            self.click(self.mouse_positions["button_change_price"])
            self.typewrite(order_price)

        self.click(self.mouse_positions["button_create_order"])
        self.sleep(.1)

    def reset_my_orders(self):
        self.click(self.mouse_positions["button_reset_my_orders"])
        self.sleep(.3)

    def next_my_orders_page(self):
        self.click(self.mouse_positions["button_next_my_ordes_page"])
        self.sleep(.1)

    def change_duration(self):
        #self.click(self.mouse_positions["button_duration"])
        self.sleep(.2)
