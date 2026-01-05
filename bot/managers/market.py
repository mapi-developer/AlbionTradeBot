from ..core import WindowCapture, InputSender
from ..managers import SettingsManager
import random


class MarketManager(InputSender):
    def __init__(self, capture: WindowCapture = None, settings: SettingsManager = None):
        super().__init__()
        if capture is None: 
            capture = WindowCapture("Albion Online Client")
        if settings is None: 
            settings = SettingsManager()

        self.capture = capture
        self.settings = settings
        
        # Load heavy dictionaries
        self.resolution = capture.get_window_resolution()
        w_h = self.resolution.split("x")
        self.width, self.height = int(w_h[0]), int(w_h[1])
        self.capture_positions = self.settings.CAPTURE_POSITIONS[self.resolution]["market"]
        self.mouse_positions = self.settings.MOUSE_POSITIONS[self.resolution]["market"]
        self.items = {item["UniqueName"]: item for item in self.settings.ITEM_DATA}
        self.lang = "EN-US" 

    def destroy(self):
        """
        Clears references and releases resources for clean deletion.
        """
        print("Destroying MarketManager...")
        
        # 1. Release WindowCapture if it has a release method
        if self.capture and hasattr(self.capture, 'release'):
            self.capture.release()
            
        # 2. Clear heavy dictionaries to free memory immediately
        if hasattr(self, 'items'):
            self.items.clear()
        
        self.capture_positions = None
        self.mouse_positions = None
        self.items = None
        
        # 3. Break references to other managers
        self.capture = None
        self.settings = None
        
        print("MarketManager destroyed.")

    def get_name_from_unique(self, unique_name: str) -> str | None:
        if unique_name in self.items:
            return self.items[unique_name]["LocalizedNames"].get(self.lang, "Language not found")
        return None

    def get_market_title(self) -> str | None:
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
    
    def order_exists(self) -> bool:
        return "edit" in self.capture.get_text_from_screenshot(self.capture_positions["order_exists"])
    
    def remove_order(self, amount: int = 10):
        self.click(self.mouse_positions["button_remove_order"], amount, interval=0.1)

    def check_pages(self) -> None:
        self.click(self.mouse_positions["next_page"], clicks=7, interval=0.2)
        self.sleep(0.5)

    def check_item_stats(self) -> None:
        if self.capture.get_text_from_screenshot(self.capture_positions["stats"]) != "sell orders":
            self.click(self.mouse_positions["button_extend_item_statistic"])
            self.sleep(0.5)

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

    def open_item(self) -> None:
        self.click(self.mouse_positions["button_buy"])
        self.check_item_stats()
        self.sleep(0.5)

    def close_item(self) -> None:
        self.click(self.mouse_positions["button_close_order_popup"])
        self.sleep(0.5)

    def buy_item(self, amount: int = 10, fast_buy: bool = False, fast_buy_price: int = 1) -> None:
        self.click(self.mouse_positions["button_buy_order"])
        self.click(self.mouse_positions["button_change_amount"])
        self.click(self.mouse_positions["button_amount_more"], clicks=amount-1)

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

    def prepare(self):
        self.change_tab("buy")
        self.click(self.mouse_positions["quality"])
        self.click(self.mouse_positions["quality_good"])
        self.change_tab("create_buy_order")