import os, sys
import json

if getattr(sys, 'frozen', False):
    # If running as a compiled .exe, use the executable's directory
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If running as a script, use the project root relative to this file
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json_config(filename):
    """Loads a JSON file from the config directory."""
    config_path = os.path.join(BASE_DIR, 'config/static', filename) 
    with open(config_path, 'r', encoding="utf-8") as f:
        return json.load(f)

class SettingsManager:
    MOUSE_POSITIONS = load_json_config('mouse_positions.json')
    ITEM_DATA = load_json_config('items.json')
    CAPTURE_POSITIONS = load_json_config('capture_positions.json')
    ITEMS_BLACK_MARKET = load_json_config('black_market_items_dictionary.json')
    
    MARKETS = [
        "fort_sterling",
        "lymhurst",
        "bridgewatch",
        "martlock",
        "thetford",
        "brecilien",
        "black_market",
    ]

    AVALIABLE_LANGUAGES = [
        "EN-US",
        "DE-DE",
        "FR-FR",
        "RU-RU",
        "PL-PL",
        "ES-ES",
        "PT-BR",
        "IT-IT",
        "ZH-CN",
        "KO-KR",
        "JA-JP",
        "ZH-TW",
        "ID-ID",
        "TR-TR",
        "AR-SA"
    ]

    CITIES = {
        "caerleon": "Caerleon",
        "martlock": "Martlock",
        "lymhurst": "Lymhurst",
        "fort_sterling": "Fort Sterling",
        "bridgewatch": "Bridgewatch",
        "thetford": "Thetford",
        "brecilien": "Brecilien",
    }

    DEFAULT_SETTINGS = {
        "general": {
            "min_silver": 1000000,
            "game_language": "RU-RU",
            "buy_mode": "order",
        },
        "fast_buy": {
            "min_profit_rate": 25,
            "default_build_amount": 15,
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
            "default_build_amount": 25,
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

    API_URL = "https://trade-backend-service-1054089939982.europe-west4.run.app"
    ITEMS_JSON_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json"
    CACHE_FILE = os.path.join(BASE_DIR, "config/static", "items.json")
    BOT_ITEMS_FILE = os.path.join(BASE_DIR, "config/static", "bot_items.json")

    BOT_LOOP_FILE = os.path.join(BASE_DIR, "config/settings", "bot_loop.json")
    SETTINGS_FILE = os.path.join(BASE_DIR, "config/settings", "settings.json")
    PRESETS_DIR = os.path.join(BASE_DIR, "config/settings", "presets")

    TRAVALER_BANNERS = [
        os.path.join(BASE_DIR, "config/static/img/travaler_icons", "island_travaler_banner.png")
    ]

    def __init__(self):
        self.ensure_directories()
        self.settings = self.load_settings()

    def ensure_directories(self):
        if not os.path.exists("config"):
            os.makedirs("config")
        if not os.path.exists(self.PRESETS_DIR):
            os.makedirs(self.PRESETS_DIR)

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
