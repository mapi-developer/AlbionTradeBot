import sys, os
import threading
import asyncio
sys.path.append(os.path.abspath(__file__))
from NewStructure.classes.player import LocalPlayer
from gui.components import BotOverlay
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

local_player = LocalPlayer()
sniffer = Sniffer(local_player)
sniffer_thread = threading.Thread(target=sniffer.start, daemon=True)
sniffer_thread.start()
settings = SettingsHandler()
overlay = BotOverlay()
bot = Bot(sniffer, settings, overlay, local_player)
wait_for_user_input()
asyncio.run(bot._run_task(bot.check_price_orders))
