import sys, os
import threading
sys.path.append(os.path.abspath(__file__))
from NewStructure.bot import Bot
from NewStructure.net import Sniffer
from NewStructure.handlers import SettingsHandler

sniffer = Sniffer()
sniffer_thread = threading.Thread(target=sniffer.start, daemon=True)
sniffer_thread.start()
settings = SettingsHandler()
bot = Bot(sniffer, settings)
print("ok")