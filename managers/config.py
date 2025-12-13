import json
import os
import flet as ft

def load_json_config(filename):
    """Loads a JSON file from the config directory."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', filename)
    with open(config_path, 'r', encoding="utf-8") as f:
        return json.load(f)

ITEMS_JSON_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json"
CACHE_FILE = "items.json"

BOT_ITEMS_FILE = "config/bot_items.json"
BOT_LOOP_FILE = os.path.join("config", "bot_loop.json") # New file for storing the sequence
DB_URL = "postgresql://albion_user:albion_password@127.0.0.1:5438/albion_market"
CONFIG_FILE = os.path.join("config", "settings.json")
PRESETS_DIR = os.path.join("config", "presets")

DEFAULT_SETTINGS = {
    "general": {
        "min_profit_rate_fast": 0.5,
        "min_profit_rate_order": 0.2,
        "default_but_amount": 1,
        "min_silver": 500000,
        "buy_mode": "order"
    },
    "city_presets": {
        "fort_sterling": "",
        "lymhurst": "",
        "bridgewatch": "",
        "martlock": "",
        "thetford": "",
        "caerleon": "",
        "brecilien": ""
    },
    "buy_logic": []
}

MOUSE_POSITIONS = load_json_config('mouse_positions.json')
ITEM_DATA = load_json_config('items.json')
CAPTURE_POSITIONS = load_json_config('capture_positions.json')
ITEMS_TO_BUY = load_json_config('items_to_buy.json')
ITEMS_BLACK_MARKET = load_json_config('black_market_items_dictionary.json')
LANGUAGE = "EN-US"

BUY_MODES = [
    ft.dropdown.Option("fast", "Fast Buy"),
    ft.dropdown.Option("order", "Order Buy"),
]

class ConfigManager:
    def __init__(self):
        self.ensure_directories()
        self.settings = self.load_settings()

    def ensure_directories(self):
        if not os.path.exists("config"):
            os.makedirs("config")
        if not os.path.exists(PRESETS_DIR):
            os.makedirs(PRESETS_DIR)

    def load_settings(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_SETTINGS

    def save_settings(self, new_settings):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(new_settings, f, indent=4)
            self.settings = new_settings
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings(self.settings)

    def get_presets_list(self):
        if not os.path.exists(PRESETS_DIR):
            return []
        return [f for f in os.listdir(PRESETS_DIR) if f.endswith(".json")]

    # --- New Methods for Bot Loop ---
    def load_bot_loop(self):
        if not os.path.exists(BOT_LOOP_FILE):
            return []
        try:
            with open(BOT_LOOP_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def save_bot_loop(self, loop_data):
        try:
            with open(BOT_LOOP_FILE, "w") as f:
                json.dump(loop_data, f, indent=4)
        except Exception as e:
            print(f"Error saving bot loop: {e}")