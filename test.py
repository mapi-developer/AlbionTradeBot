import sys, os
import threading
sys.path.append(os.path.abspath(__file__))
from NewStructure.bot import Bot
from NewStructure.net import Sniffer
from NewStructure.handlers import SettingsHandler
import time


def wait_for_user_input():
    global run
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        run = False
        return


sniffer = Sniffer()
sniffer_thread = threading.Thread(target=sniffer.start, daemon=True)
sniffer_thread.start()
settings = SettingsHandler()
bot = Bot(sniffer, settings)
wait_for_user_input()
print(bot.market_handler.get_market_title())