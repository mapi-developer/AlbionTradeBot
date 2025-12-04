import json
import os

CONFIG_FILE = os.path.join("config", "settings.json")
PRESETS_DIR = os.path.join("config", "presets")

# Default Settings Structure
DEFAULT_SETTINGS = {
    "min_profit_rate": 15,
    "min_silver_to_stop": 500000,
    "buy_items_preset_fort_sterling": "",
    "buy_items_preset_lymhurst": "",
    "buy_items_preset_bridgewatch": "",
    "buy_items_preset_martlock": "",
    "buy_items_preset_thetford": "",
    "buy_items_preset_caerleon": "",
    "buy_items_preset_brecilien": "",
    "buy_amount_under_1k": "",
    "buy_amount_under_10k": "",
    "buy_amount_under_50k": "",
    "buy_amount_under_100k": "",
    "buy_amount_under_200k": "",
    "buy_amount_under_1m": "",
}

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