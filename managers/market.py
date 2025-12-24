from core.capture import WindowCapture
from core.input import InputSender
from .config import MOUSE_POSITIONS, CAPTURE_POSITIONS, ITEM_DATA, ConfigManager, LANGUAGE

class MarketManager(InputSender):
    def __init__(self, capture: WindowCapture = None, config: ConfigManager = None):
        super().__init__()
        if capture == None:
            capture = WindowCapture(window_name="Albion Online Client")
        if config == None:
            config = ConfigManager()
        self.mouse_positions = MOUSE_POSITIONS[capture.get_window_resolution()]["market"]
        self.capture_positions = CAPTURE_POSITIONS[capture.get_window_resolution()]["market"]
        self.items = { item["UniqueName"]: item for item in ITEM_DATA }
        self.capture = capture
        self.config = config
        #self.lang = config.get("general")["game_language"]
        self.lang = LANGUAGE

    def __repr__(self) -> str:
        return f"MarketManager: {self.mouse_positions["search"]}"
    
    def get_market_title(self) -> str:
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
        else:
            return "Error To Check Market"

    def order_exists(self) -> bool:
        return self.capture.get_text_from_screenshot(self.capture_positions["order_exists"]) == "edit"

    def remove_order(self, amount: int = 10):
        self.click(self.mouse_positions["button_remove_order"], amount, interval=0.1)

    def check_pages(self) -> None:
        self.click(self.mouse_positions["next_page"], clicks=5, interval=0.2)
        self.sleep(0.5)
    
    def get_name_from_unique(self, unique_name: str) -> str | None:
        if unique_name in self.items:
            return self.items[unique_name]["LocalizedNames"].get(self.lang, "Language not found")
        return None
    
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
            if name_from_unique != None:
                name = name_from_unique

        self.click(self.mouse_positions["search_reset"])
        self.click(self.mouse_positions["search"])
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

        self.sleep(0.5)

    def prepare(self):
        self.change_tab("buy")
        self.click(self.mouse_positions["quality"])
        self.click(self.mouse_positions["quality_good"])
        self.change_tab("create_buy_order")
