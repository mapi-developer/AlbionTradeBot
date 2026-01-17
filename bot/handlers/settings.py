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
        self.LOGS_DIR = os.path.join(BASE_DIR, "config/logs")
        self.BOT_LOOP_FILE = os.path.join(BASE_DIR, "config/settings", "bot_loop.json")
        self.SETTINGS_FILE = os.path.join(BASE_DIR, "config/settings", "settings.json")
        self.PRESETS_DIR = os.path.join(BASE_DIR, "config/settings", "presets")
        self.MOUSE_POSITIONS = load_json_config("mouse_positions.json")
        self.CAPTURE_POSITIONS = load_json_config("capture_positions.json")
        self.ITEMS_BLACK_MARKET = load_json_config('black_market_items_dictionary.json')
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
        self.DEFAULT_SETTINGS = {
            "general": {
                "min_silver": 1000000,
                "game_language": "EN-US",
                "buy_mode": "order",
            },
            "fast_buy": {
                "min_profit_rate": 25,
                "default_build_amount": 10,
                "presets": {
                    "fort_sterling": "",
                    "lymhurst": "",
                    "bridgewatch": "",
                    "martlock": "",
                    "thetford": "",
                    "caerleon": "",
                    "brecilien": ""
                },
                "buy_logic": []
            },
            "order_buy": {
                "min_profit_rate": 60,
                "default_build_amount": 10,
                "presets": {
                    "fort_sterling": "",
                    "lymhurst": "",
                    "bridgewatch": "",
                    "martlock": "",
                    "thetford": "",
                    "caerleon": "",
                    "brecilien": ""
                },
                "buy_logic": []
            },
        }
        self.settings = self.load_settings()
        self.SPECIAL_ITEMS_BM = {
            "2452": 2,
            "2831": 2,
            "8473": 1,
            "6239": 2,
            "6843": 2,
            "1997": 1,
            "2149": 2,
            "3383": 2,
            "3410": 2,
            "3437": 2,
            "3990": 1,
            "4018": 1,
            "4046": 1,
            "4598": 2,
            "4625": 2,
            "4652": 2,
            "2910": 3,
            "9076": 3,
            "8875": 3,
            "9277": 3,
            "6440": 3,
            "7848": 3,
            "8069": 3,
            "8674": 3,
            "9478": 3,
            "7647": 3,
            "2300": 3,
            "7446": 3,
            "7245": 3,
            "7044": 3,
            "6641": 3,
        }
        self.SPECIAL_ITEMS = {
            "Shield": 1,
            "Mercenary Hood": 1,
            "Mercenary Jacket": 1,
            "Mercenary Shoes": 1,
            "Broadsword": 1,
            "Tome of Spells": 2,
            "Cape": 2,
            "Bag": 2,
            "Soldier Helmet": 2,
            "Soldier Armor": 2,
            "Soldier Boots": 2,
            "Scholar Cowl": 2,
            "Scholar Robe": 2,
            "Scholar Sandals": 2,
            "Bow": 2,
            "Fire Staff": 2,
            "Torch": 3,
            "Crossbow": 3,
            "Cursed Staff": 3,
            "Fire Staff": 3,
            "Frost Staff": 3,
            "Arcane Staff": 3,
            "Holy Staff": 3,
            "Nature Staff": 3,
            "Dagger": 3,
            "Spear": 3,
            "Battleaxe": 3,
            "Quarterstaff": 3,
            "Hammer": 3,
            "Mace": 3,
            "Brawler Gloves": 3,
            "Prowling Staff": 3,
        }

        self.API_URL = "https://trade-backend-service-1054089939982.europe-west4.run.app"
        self.GOOGLE_CLIENT_ID = "1054089939982-e2umo92u5p7mh4gjm3hvknddprenho3k.apps.googleusercontent.com"
        self.DISCORD_CLIENT_ID = "1447721013260456058"

    def load_settings(self):
        if not os.path.exists(self.SETTINGS_FILE):
            self.save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return self.DEFAULT_SETTINGS

    def save_settings(self, new_settings):
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(new_settings, f, indent=4)
            self.settings = new_settings
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_location_graph(self, location_id: str) -> WaypointGraph:
        if location_id == '': return WaypointGraph()
        locations = load_json_config("locations.json")
        return WaypointGraph().from_dict(locations.get(location_id))
    
    def get(self, key):
        return self.settings.get(key, self.DEFAULT_SETTINGS.get(key))
    
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings(self.settings)

    def get_presets_list(self):
        if not os.path.exists(self.PRESETS_DIR):
            return []
        return [f for f in os.listdir(self.PRESETS_DIR) if f.endswith(".json")]

    def load_bot_loop(self):
        if not os.path.exists(self.BOT_LOOP_FILE):
            return []
        try:
            with open(self.BOT_LOOP_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def save_bot_loop(self, loop_data):
        try:
            with open(self.BOT_LOOP_FILE, "w") as f:
                json.dump(loop_data, f, indent=4)
        except Exception as e:
            print(f"Error saving bot loop: {e}")

    def get_logs(self):
        """Returns a list of log filenames, sorted by newest first."""
        if not os.path.exists(self.LOGS_DIR):
            return []
        try:
            files = [f for f in os.listdir(self.LOGS_DIR) if f.endswith('.json')]
            files.sort(reverse=True)
            return files
        except Exception as e:
            print(f"Error listing logs: {e}")
            return []

    def get_log(self, filename):
        """Returns the content of a specific log file as a list/dict."""
        path = os.path.join(self.LOGS_DIR, filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading log {filename}: {e}")
            return []

    def delete_log(self, filename):
        """Deletes a specific log file."""
        path = os.path.join(self.LOGS_DIR, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                print(f"Error deleting log {filename}: {e}")
                return False
        return False
