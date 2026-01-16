import os
import sys
import json
from ..core import WaypointGraph

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json_config(filename):
    """Loads a JSON file from the config directory."""
    config_path = os.path.join(BASE_DIR, 'config/static', filename) 
    with open(config_path, 'r', encoding="utf-8") as f:
        return json.load(f)


class SettingsHandler:
    def __init__(self):
        self.MOUSE_POSITIONS = load_json_config("mouse_positions.json")
        self.CAPTURE_POSITIONS = load_json_config("capture_positions.json")
        self.ITEM_DATA = load_json_config('items.json')
        self.MARKET_TITLES = {
            "4002": "fort_sterling",
            "1002": "lymhurst",
            "2004": "bridgewatch",
            "3004": "martlock",
            "0007": "thetford",
            "5003": "brecilien",
            "3003": "black_market",
            "3005": "caerleon",
        }

    def get_location_graph(self, location_id: str) -> WaypointGraph:
        if location_id == '': return WaypointGraph()
        locations = load_json_config("locations.json")
        return WaypointGraph().from_dict(locations.get(location_id))