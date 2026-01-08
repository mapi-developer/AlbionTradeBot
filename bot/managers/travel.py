from ..core import InputSender
from ..core import WindowCapture
from ..managers import SettingsManager

class TravelManager(InputSender):
    def __init__(self, bot, capture: WindowCapture = None, settings: SettingsManager = None):
        super().__init__()
        if bot == None: return
        if capture == None: capture = WindowCapture("Albion Online Client")
        if settings == None: settings = SettingsManager()

        self.bot = bot
        self.capture = capture
        self.settings = settings
        self.capture_positions = self.settings.CAPTURE_POSITIONS[capture.get_window_resolution()]["travel"]
        self.mouse_positions = self.settings.MOUSE_POSITIONS[capture.get_window_resolution()]["travel"]
    
    def from_island_to_chest(self):
        self.click(self.mouse_positions["character_middle"])
        self.press("enter")
        self.sleep(.3)
        self.typewrite("#forcecityoverload true")
        self.press("enter")
        pos = self.mouse_positions["from_travaler_to_chest"]
        print(pos)
        self.click([pos[0], pos[1]])
        self.sleep(pos[2])
        print("ok")

    def from_island_chest_to_black_market(self):
        for i, item in enumerate(self.mouse_positions["from_island_chest_to_travaler"]):
            if i+1 == len(self.mouse_positions["from_island_chest_to_travaler"]):
                self.click([item[0], item[1]])
            else:
                self.right_click([item[0], item[1]])
            self.sleep(item[2])
            self.bot._wait_if_paused()

        self.choose_destination("black_market")
        self.from_travel_to_market("black_market")

    def from_island_to_traveler(self):
        self.click(self.mouse_positions["character_middle"])
        self.press("enter")
        self.sleep(.3)
        self.typewrite("#forcecityoverload true")
        self.sleep(.3)
        self.press("enter")
        travaler_location = self.capture.find_template(self.settings.TRAVALER_BANNERS)
        if travaler_location != None:
            self.click(travaler_location)
        else:
            print("[Error] Failed to find travaler banner location")
        self.sleep(3)

    def from_market_to_travaler(self):
        destination = self.bot.current_location
        self.press("esc")
        for i, item in enumerate(self.mouse_positions["from_"+destination]):
            if i+1 == len(self.mouse_positions["from_"+destination]):
                self.click([item[0], item[1]])
            else:
                self.right_click([item[0], item[1]])
            self.sleep(item[2])
            self.bot._wait_if_paused()

    def from_travel_to_market(self, destination: str):
        self.press("esc")
        for i, item in enumerate(self.mouse_positions["to_"+destination]):
            if i+1 == len(self.mouse_positions["to_"+destination]):
                self.click([item[0], item[1]])
            else:
                self.right_click([item[0], item[1]])
            self.sleep(item[2])
            self.bot._wait_if_paused()

        self.bot.current_location = destination

    def choose_destination(self, destination: str):
        if destination in self.settings.MARKETS:
            self.click(self.mouse_positions[destination+"_section"])
        else:
            self.click(self.mouse_positions["to_search"])
            self.typewrite(destination)
            self.click(self.mouse_positions["first_island_from_search"])
        self.click(self.mouse_positions["buy_journey"])
        self.sleep(5)

    def travel_to(self, destination: str):
        print(f"Start Travel to: {destination}")
        if self.bot.current_location in self.settings.MARKETS:
            self.from_market_to_travaler()
        elif self.bot.current_location == "island":
            self.from_island_to_traveler()
        elif self.bot.current_location == "guild_chest_caerleon":
            for i, item in enumerate(self.mouse_positions["from_island_chest_to_travaler"]):
                if i+1 == len(self.mouse_positions["from_island_chest_to_travaler"]):
                    self.click([item[0], item[1]])
                else:
                    self.right_click([item[0], item[1]])
                self.sleep(item[2])
                self.bot._wait_if_paused()
        
        self.choose_destination(destination=destination)
        self.bot.current_location = "island"

        if destination in self.settings.MARKETS or destination == "brecilien":
            self.from_travel_to_market(destination=destination)

        self.sleep(1)
