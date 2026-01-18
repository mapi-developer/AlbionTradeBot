from ..classes.player import LocalPlayer
from ..core import InputSender, WindowCapture, WaypointGraph
from .settings import SettingsHandler
from typing import TYPE_CHECKING
import time
import math

if TYPE_CHECKING:
    from ..bot import Bot

MARKET_LOCATIONS = ["4002", "1002", "2004", "3008", "0007", "5003", "3003", "3005"]

CONNECTED_LOCATIONS = {
    "4002": "4000",
    "1002": "1000",
    "2004": "2000",
    "3008": "3004",
    "0007": "0000",
    "5003": "5000",
    "3005": "3003",
    "3003": "3003",
}


class TravelHandler(InputSender):
    current_location_graph: WaypointGraph

    def __init__(
        self,
        bot: "Bot",
        capture: WindowCapture,
        settings: SettingsHandler,
        local_player: LocalPlayer,
    ):
        super().__init__()
        self.bot = bot
        self.settings = settings
        self.capture = capture
        self.local_player = local_player
        self.mouse_positions = self.settings.MOUSE_POSITIONS[
            capture.get_window_resolution()
        ]["travel"]
        self.current_location_graph = self.settings.get_location_graph(
            self.local_player.location.location_id
        )
        self.current_keys = []
        self.location = ""
        self.can_move = True

    def on_join_finished(self, status: bool):
        self.sleep(2)
        self.can_move = status

    def on_location_changed(
        self, location_id: str, location_type: str, location_name: str
    ):
        if location_type != "":
            cutoff, separator, last_part = location_type.rpartition("-")
            if "GUILD" in cutoff:
                location_id = "ISLAND-GUILD"
            else:
                location_id = cutoff
        self.location = location_id
        self.current_location_graph = self.settings.get_location_graph(location_id)

    def release_all_keys(self):
        for key in ["up", "down", "left", "right"]:
            self.key_up(key)
        self.current_keys = []

    def update_movement_keys(self, target_angle):
        directions = [
            (357, ["down", "right"]),  # North-East
            (42, ["right"]),  # East
            (87, ["up", "right"]),  # South-East
            (132, ["up"]),  # South
            (177, ["up", "left"]),  # South-West
            (222, ["left"]),  # West
            (267, ["down", "left"]),  # North-West
            (312, ["down"]),  # North
        ]

        best_keys = []
        min_diff = 360

        for angle, keys in directions:
            diff = abs(angle - target_angle)
            if diff > 180:
                diff = 360 - diff
            if diff < min_diff:
                min_diff = diff
                best_keys = keys

        if set(best_keys) != set(self.current_keys):
            for key in self.current_keys:
                if key not in best_keys:
                    self.key_up(key)
            for key in best_keys:
                if key not in self.current_keys:
                    self.key_down(key)
            self.current_keys = best_keys

    def choose_destination(self, destination: str):
        self.sleep(1)
        if destination in CONNECTED_LOCATIONS.values() and destination != "5000":
            self.click(self.mouse_positions[destination+"_section"])
            self.sleep(.3)
        else:
            if destination == "5000":
                destination = "Brecilien"
            self.click(self.mouse_positions["to_search"])
            self.typewrite(destination)
            self.sleep(.2)
            self.click(self.mouse_positions["first_island_from_search"])
        self.click(self.mouse_positions["buy_journey"])
        self.can_move = False

    async def move_to_position(self, target_position: list[float], tolerance=3, timeout=15):
        start_time = time.time()
        try:
            while True:
                await self.bot._wait_for_resume()
                current_position = self.local_player.position
                if not current_position:
                    time.sleep(0.1)
                    continue

                dx = target_position[0] - current_position.x
                dy = target_position[1] - current_position.y
                dist = math.hypot(dx, dy)

                if dist <= tolerance:
                    self.release_all_keys()
                    return True

                if time.time() - start_time > timeout:
                    print(f"[TravelHandler] Timeout reaching {target_position}")
                    self.release_all_keys()
                    return False

                angle_rad = math.atan2(dy, dx)
                target_angle = math.degrees(angle_rad)
                if target_angle < 0:
                    target_angle += 360

                self.update_movement_keys(target_angle)
                time.sleep(0.01)
        except:
            self.release_all_keys()
            pass

    async def move_to_node(self, target_node_id: int):
        self.capture.set_foreground_window()
        closest_node_id = self.current_location_graph.get_closest_node(
            self.local_player.position.to_list()
        )
        path = self.current_location_graph.find_path(
            closest_node_id[0], target_node_id
        )
        for waypoint in path:
            await self.move_to_position(waypoint)

    async def move_to_planner(self):
        if self.location == "": return
        if self.location in MARKET_LOCATIONS and self.location != "3003":
            await self.move_to_node(1)
            self.right_click(self.mouse_positions[f"{self.location}_gate"])
            self.can_move = False
        while not self.can_move:
            self.sleep(0.1)
        if self.location in ["4000", "1000"]:
            await self.move_to_node(2)
        else:
            await self.move_to_node(1)
        self.click(self.mouse_positions[f"{self.location}_planner"])

    async def move_to_guild_chest(self):
        while not self.can_move:
            self.sleep(0.1)
        if self.location != "ISLAND-GUILD":
            return
        await self.move_to_node(3)
        self.click(self.mouse_positions["ISLAND-GUILD_chest"])
        self.sleep(2)

    async def move_to_market(self, destination_market: str):
        self.press("esc")
        if self.location == "": return
        while self.current_location_graph == None:
            self.sleep(0.1)
        if self.location in CONNECTED_LOCATIONS.values() and self.location == CONNECTED_LOCATIONS.get(destination_market):
            if destination_market == "3005":
                node_id = 5
            else:
                node_id = len(self.current_location_graph.nodes)
            await self.move_to_node(node_id)
            if destination_market != "3003":
                self.key_down("up")
                self.sleep(2)
                self.key_up("up")
                self.can_move = False
        while not self.can_move:
            self.sleep(0.1)
        if self.location == destination_market:
            if destination_market == "3005":
                node_id = 4
            else:
                node_id = len(self.current_location_graph.nodes)
            await self.move_to_node(node_id)
            self.click(self.mouse_positions[f"{self.location}_market"])
        else:
            await self.move_to_planner()
            self.choose_destination(CONNECTED_LOCATIONS.get(destination_market))
            while not self.can_move:
                self.sleep(0.1)
            await self.move_to_market(destination_market)
    
    async def move_to_island(self, destination_island: str):
        self.press("esc")
        await self.move_to_planner()
        self.choose_destination(destination_island)