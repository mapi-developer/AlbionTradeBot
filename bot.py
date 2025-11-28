from managers.market import MarketManager
from core.capture import WindowCapture
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

capture = WindowCapture(base_dir=BASE_DIR, window_name="Albion Online Client")
capture.set_foreground_window()
market_manager = MarketManager()

market_manager.change_tab("buy")
market_manager.search_item("Royal robe")
market_manager.open_item()
market_manager.buy_item(amount=10)
