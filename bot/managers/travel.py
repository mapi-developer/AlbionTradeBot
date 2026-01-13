from ..core import InputSender
from ..core import WindowCapture
from ..managers import SettingsManager
import math

class TravelManager(InputSender):
    def __init__(self, bot, capture: WindowCapture = None, settings: SettingsManager = None, island_name = None):
        super().__init__()
        if bot == None: return
        if capture == None: capture = WindowCapture("Albion Online Client")
        if settings == None: settings = SettingsManager()

        self.island_name = island_name
        self.bot = bot
        self.capture = capture
        self.settings = settings
        self.capture_positions = self.settings.CAPTURE_POSITIONS[capture.get_window_resolution()]["travel"]
        self.mouse_positions = self.settings.MOUSE_POSITIONS[capture.get_window_resolution()]["travel"]

    def calculate_click_position(self, current_pos, target_pos, click_radius=200):
        """
        Converts 3D world coordinates to 2D screen coordinates for navigation.
        Based on Albion's 45-degree isometric projection.
        
        Args:
            current_pos (list/tuple): [x, y] of the character.
            target_pos (list/tuple): [x, y] of the destination.
            click_radius (int): Distance in pixels from screen center to click.
        """
        # 1. Get Screen Center
        # Use configured center or default to 1920x1080 center
        #center_pos = self.settings.SCREEN_CENTER[self.capture.get_window_resolution()]
        res = self.capture.get_window_resolution() # e.g. (1920, 1080)
        if res:
            width, height = res.split("x")
        center_x, center_y = [int(int(width) * 0.5), int(int(height) * 0.44)]

        # 2. Calculate World Deltas
        world_dx = target_pos[0] - current_pos[0]
        world_dy = target_pos[1] - current_pos[1]

        # 3. Apply Isometric Projection
        # Screen X = Sum of World Axes (Rotated 45 deg)
        # Screen Y = Difference of World Axes (Rotated 45 deg)
        # 0.8 pr 0.722
        screen_dx = (world_dx + world_dy)
        screen_dy = (world_dx - world_dy) * 0.75 # sin(45) squash factor

        # 4. Normalize to Click Radius
        # We essentially create a unit vector for the screen direction, 
        # then multiply by our desired click radius.
        length = math.hypot(screen_dx, screen_dy)
        
        # Prevent division by zero if target is too close
        if length < 0.1:
            return [center_x, center_y]

        scale = click_radius / length
        
        final_screen_x = screen_dx * scale
        final_screen_y = screen_dy * scale

        # 5. Offset from Center
        # We add to center because screen coordinates start top-left (0,0)
        click_x = int(center_x + final_screen_x)
        click_y = int(center_y + final_screen_y)

        return [click_x, click_y]

    def move_step(self, next_waypoint):
        my_pos = self.bot.sniffer.get_current_position()
        
        # Calculate click point
        click_coords = self.calculate_click_position(my_pos, next_waypoint)
        
        # Perform the click
        print(f"Moving from {my_pos} to {next_waypoint} -> Click: {click_coords}")
        self.right_click(click_coords)

    def get_island(self):
        if self.island_name.value == None:
            return None
        island = self.island_name.value
        
        if any(word in island.lower() for word in ["fort", "sterling"]) and "guild" in island.lower():
            return "fort_sterling_guild"
        elif any(word in island.lower() for word in ["fort", "sterling"]) and not "guild" in island.lower():
            return "fort_sterling_personal"
        elif any(word in island.lower() for word in ["lymhurst"]) and "guild" in island.lower():
            return "lymhurst_guild"
        elif any(word in island.lower() for word in ["lymhurst"]) and not "guild" in island.lower():
            return "lymhurst_personal"
        elif any(word in island.lower() for word in ["bridgewatch"]) and "guild" in island.lower():
            return "bridgewatch_guild"
        elif any(word in island.lower() for word in ["bridgewatch"]) and not "guild" in island.lower():
            return "bridgewatch_personal"
        elif any(word in island.lower() for word in ["martlock"]) and "guild" in island.lower():
            return "martlock_guild"
        elif any(word in island.lower() for word in ["martlock"]) and not "guild" in island.lower():
            return "martlock_personal"
        elif any(word in island.lower() for word in ["thetford"]) and "guild" in island.lower():
            return "thetford_guild"
        elif any(word in island.lower() for word in ["thetford"]) and not "guild" in island.lower():
            return "thetford_personal"
        elif any(word in island.lower() for word in ["caerleon"]) and "guild" in island.lower():
            return "caerleon_guild"
        elif any(word in island.lower() for word in ["caerleon"]) and not "guild" in island.lower():
            return "caerleon_personal"
        elif any(word in island.lower() for word in ["brecilien"]) and not "guild" in island.lower():
            return "brecilien_personal"
        else:
            return None
    
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
        #travaler_location = self.capture.find_template(self.settings.TRAVALER_BANNERS)
        travaler_location = self.mouse_positions[f"{self.get_island()}_planner"]
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
