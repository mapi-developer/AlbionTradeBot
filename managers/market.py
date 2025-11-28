from core.capture import WindowCapture
from core.input import InputSender
from config import MOUSE_POSITIONS, CAPTURE_POSITIONS, ITEM_DATA, LANGUAGE

class MarketManager(InputSender):
    def __init__(self, capture: WindowCapture = None):
        super().__init__()
        if capture == None:
            capture = WindowCapture(window_name="Albion Online Client")
        self.mouse_positions = MOUSE_POSITIONS["2560x1600"]["market"]
        self.capture_positions = CAPTURE_POSITIONS["2560x1600"]["market"]
        self.items = { item["UniqueName"]: item for item in ITEM_DATA }
        self.capture = capture
        self.lang = LANGUAGE

    def __repr__(self) -> str:
        return f"MarketManager: {self.mouse_positions["search"]}"
    
    def get_name_from_unique(self, unique_name) -> str | None:
        if unique_name in self.items:
            return self.items[unique_name]["LocalizedNames"].get(self.lang, "Language not found")
        return None
    
    def check_item_stats(self) -> None:
        if self.capture.get_text_from_screenshot(self.capture_positions["stats"]) != "sell orders":
            self.click(self.mouse_positions["button_extend_item_statistic"])
            self.sleep(0.5)
        
    def search_item(self, name: str, from_db: bool = False) -> None:
        if from_db == True:
            name_from_unique = self.get_name_from_unique(name)
            if name_from_unique != None:
                name = self.get_name_from_unique(name)

        self.click(self.mouse_positions["search_reset"])
        self.click(self.mouse_positions["search"])
        self.typewrite(name)
        self.sleep(0.5)

    def change_tab(self, name: str) -> None:
        self.click(self.mouse_positions["tab_"+name])
        self.sleep(0.5)

    def open_item(self) -> None:
        self.click(self.mouse_positions["button_buy"])
        self.check_item_stats()
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