from ..core import InputSender, WindowCapture
from .settings import SettingsHandler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import Bot

class TravelHandler(InputSender):
    def __init__(self, bot: 'Bot', capture: WindowCapture, settings: SettingsHandler):
        self.bot = bot
        self.settings = settings
        self.mouse_positions = self.settings.MOUSE_POSITIONS[capture.get_window_resolution()]["travel"]

    