from managers.market import MarketManager
from core.capture import WindowCapture
from net.sniffer import AlbionSniffer
import os
import threading
from config import ITEMS_TO_BUY

class TradeBot:
    def __init__(self, capture: WindowCapture = None, sniffer: AlbionSniffer = None, market_manager: MarketManager = None):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        if capture == None:
            capture = WindowCapture(base_dir=BASE_DIR, window_name="Albion Online Client")
        self.capture = capture
        capture.set_foreground_window()

        if self.market_manager == None:
            self.market_manager = MarketManager(capture=capture)
        self.market_manager = self.market_manager

        if self.sniffer == None:
            self.sniffer = AlbionSniffer()
        self.sniffer = self.sniffer
        self.sniffer_thread = threading.Thread(target=self.sniffer.start, daemon=True)
        self.sniffer_thread.start()

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
                        price = order.get('UnitPriceSilver', 0)
                        quality = order.get('QualityLevel', 0)
                        
                        if price < lowest_price and price > 0:
                            lowest_price = price
                            best_quality = quality

                #print(f"Captured {len(current_market_orders)} orders.")
                print(f"Lowest Price found: {lowest_price} (Quality: {best_quality})")
                self.market_manager.close_item()
        except KeyboardInterrupt:
            print("Stopping bot...")