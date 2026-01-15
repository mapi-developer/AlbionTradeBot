import asyncio
from .core import InputSender, WindowCapture
from .net import Sniffer
from .classes import LocalPlayer
from .handlers import SettingsHandler, TravelHandler, MarketHandler, LoginHandler, LogHandler, ChestHandler

class Bot:
    def __init__(self, sniffer: Sniffer, settings: SettingsHandler):
        self.sniffer = sniffer
        self.settings = settings
        self.input_sender = InputSender()
        self.capture = WindowCapture("Albion Online Client")
        self.log_handler = LogHandler()
        self.login_handler = LoginHandler()
        self.market_handler = MarketHandler()
        self.travel_handler = TravelHandler(self, self.capture, self.settings)
        self.chest_handler = ChestHandler()

        self._can_run = asyncio.Event()
        self._can_run.set()

    def pause(self):
        print("[Bot] pausing...")
        self._can_run.clear()

    def resume(self):
        print("[Bot] resuming...")
        self._can_run.set()

    def toggle_pause(self):
        if self._can_run.is_set():
            self.pause()
            return True
        else:
            self.resume()
            return False

    def travel_to(self):
        pass

    def check_price_fast(self):
        pass

    def check_price_orders(self):
        pass

    def buy_items(self):
        pass

    def update_orders(self):
        pass

    def remove_orders(self):
        pass

    def sell_items(self):
        pass

